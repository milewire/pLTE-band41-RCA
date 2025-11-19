from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# Ensure project root is on sys.path so we can import:
# - top-level `engine` and `ai` packages
# - the `backend` package itself when running from the repo root
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from engine.parser import parse_ericsson_pm_xml
    print("[INIT] Successfully imported engine.parser")
except ImportError as e:
    print(f"[INIT] Failed to import engine.parser: {e}")
    print(f"[INIT] Current working directory: {os.getcwd()}")
    print(f"[INIT] Backend directory: {backend_dir}")
    raise
from engine.rca import analyze_rca
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import gzip
import zipfile
import tempfile
import shutil
import time
from datetime import datetime, timedelta
import pandas as pd

# AI module imports (from top-level ai package)
from ai.gpt_summary import generate_ai_summary
from ai.anomaly_detector import detect_anomalies, prepare_hourly_data
from ai.drift_detector import detect_drift
from ai.nlq import answer_question
from backend.analyzers.alarm_analyzer import parse_alarm_file, summarize_alarms, alarms_to_dicts
from backend.analyzers.backhaul_analyzer import parse_backhaul_csv, summarize_backhaul
from backend.analyzers.attach_analyzer import parse_attach_csv, summarize_attach
from backend.services.pdf_generator import generate_incident_report_pdf
from backend.services.correlation_engine import (
    describe_kpi_alarm_correlation,
    describe_kpi_backhaul_correlation,
    describe_attach_failures_correlation,
)

app = FastAPI(title="LTE Band 41 RCA API", version="1.0.0")

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary storage for uploaded files
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# File retention settings (in hours)
FILE_RETENTION_HOURS = 24  # Files older than 24 hours will be deleted

# In-memory context for latest non-KPI uploads (single-tenant assumption)
LATEST_ALARM_SUMMARY: Optional[Dict[str, Any]] = None
LATEST_BACKHAUL_SUMMARY: Optional[Dict[str, Any]] = None
LATEST_ATTACH_SUMMARY: Optional[Dict[str, Any]] = None
LATEST_RCA_RESULT: Optional[Dict[str, Any]] = None


class RCAResponse(BaseModel):
    root_cause: str
    severity: str
    evidence: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]
    kpi_data: List[Dict[str, Any]]
    # AI-enhanced fields
    ai_summary: Optional[str] = None
    anomaly_detection: Optional[Dict[str, Any]] = None
    drift: Optional[Dict[str, Any]] = None


class AlarmSummaryResponse(BaseModel):
    total_count: int
    by_severity: Dict[str, int]
    by_mo: Dict[str, int]
    timeline: List[Dict[str, Any]]
    sample: List[Dict[str, Any]]


class BackhaulSummaryResponse(BaseModel):
    total_samples: int
    impairment_score: float
    modulation_trend: List[Dict[str, Any]]
    rssi_trend: List[Dict[str, Any]]
    latency_jitter_trend: List[Dict[str, Any]]
    error_summary: Dict[str, float]


class AttachSummaryResponse(BaseModel):
    overall_attach_success_rate: Optional[float]
    per_imsi: Dict[str, Dict[str, Any]]
    per_apn: Dict[str, Dict[str, Any]]
    per_tac: Dict[str, Dict[str, Any]]
    failure_categories: Dict[str, int]
    dominant_failure_category: Optional[str]


class AskAIRequest(BaseModel):
    question: str
    site: Optional[str] = None
    time_range: Optional[str] = None


class AskAIResponse(BaseModel):
    answer: str
    confidence: float




@app.get("/health")
async def health_check():
    """Health check endpoint with upload directory status"""
    health_status = {
        "status": "healthy",
        "service": "LTE Band 41 RCA API",
        "upload_dir": {
            "path": str(UPLOAD_DIR),
            "exists": UPLOAD_DIR.exists(),
            "writable": False
        }
    }
    
    # Test write permissions
    try:
        if UPLOAD_DIR.exists():
            test_file = UPLOAD_DIR / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            health_status["upload_dir"]["writable"] = True
        else:
            # Try to create it
            UPLOAD_DIR.mkdir(exist_ok=True)
            health_status["upload_dir"]["writable"] = True
    except Exception as e:
        health_status["upload_dir"]["error"] = str(e)
        health_status["status"] = "degraded"
    
    return health_status


def cleanup_old_files():
    """Remove files older than FILE_RETENTION_HOURS from uploads directory"""
    if not UPLOAD_DIR.exists():
        return
    
    cutoff_time = time.time() - (FILE_RETENTION_HOURS * 3600)
    deleted_count = 0
    
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    
    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old file(s) from uploads directory")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and store PM XML file temporarily"""
    import traceback
    
    try:
        # Validate filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Validate file extension
        if not file.filename.endswith(('.xml.gz', '.gz', '.zip', '.xml')):
            raise HTTPException(status_code=400, detail="File must be .xml.gz, .gz, .zip, or .xml format")
        
        # Ensure upload directory exists and is writable
        try:
            UPLOAD_DIR.mkdir(exist_ok=True)
            # Test write permissions
            test_file = UPLOAD_DIR / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            error_msg = f"Cannot write to uploads directory: {str(e)}"
            print(f"Upload directory error: {error_msg}")
            print(f"Upload directory path: {UPLOAD_DIR}")
            print(f"Upload directory exists: {UPLOAD_DIR.exists()}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Clean up old files before uploading new one
        try:
            cleanup_old_files()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")
            # Continue even if cleanup fails
        
        # Save file temporarily
        file_path = UPLOAD_DIR / file.filename
        
        # Check file size (limit to 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_size = 0
        
        try:
            with open(file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(8192)  # Read in 8KB chunks
                    if not chunk:
                        break
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        # Clean up partial file
                        if file_path.exists():
                            file_path.unlink()
                        raise HTTPException(
                            status_code=413, 
                            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
                        )
                    buffer.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            # Clean up partial file on error
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            error_msg = f"Failed to save file: {str(e)}"
            print(f"File save error: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        print(f"Successfully uploaded file: {file.filename} ({file_size / 1024:.2f} KB)")
        
        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": file_size,
            "message": f"File uploaded successfully. Files are retained for {FILE_RETENTION_HOURS} hours."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        print(f"Upload error: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/upload-alarms", response_model=AlarmSummaryResponse)
async def upload_alarms(file: UploadFile = File(...)):
    """
    Upload and parse FM/alarm logs (XML, CSV, or text).

    Returns a summarized view suitable for the Alarms dashboard and RCA engine.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Read entire file into memory (FM files are typically modest in size)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        records = parse_alarm_file(content, file.filename)
        summary = summarize_alarms(records)

        # Store for subsequent RCA runs (single-user/session-oriented usage)
        global LATEST_ALARM_SUMMARY
        LATEST_ALARM_SUMMARY = summary

        return AlarmSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alarm upload failed: {str(e)}")


@app.post("/upload-backhaul", response_model=BackhaulSummaryResponse)
async def upload_backhaul(file: UploadFile = File(...)):
    """
    Upload and parse backhaul CSV logs (microwave/fiber).
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        samples = parse_backhaul_csv(content)
        summary = summarize_backhaul(samples)

        global LATEST_BACKHAUL_SUMMARY
        LATEST_BACKHAUL_SUMMARY = summary

        return BackhaulSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backhaul upload failed: {str(e)}")


@app.post("/upload-attach-logs", response_model=AttachSummaryResponse)
async def upload_attach_logs(file: UploadFile = File(...)):
    """
    Upload and parse attach/ERAB logs (CSV).
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        records = parse_attach_csv(content)
        summary = summarize_attach(records)

        global LATEST_ATTACH_SUMMARY
        LATEST_ATTACH_SUMMARY = summary

        return AttachSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attach log upload failed: {str(e)}")


@app.post("/analyze", response_model=RCAResponse)
async def analyze_pm_file(file: UploadFile = File(...)):
    """Parse PM XML file and run RCA analysis with AI enhancements"""
    try:
        # Determine file type
        file_ext = file.filename.lower()
        is_zip = file_ext.endswith('.zip')
        is_gz = file_ext.endswith('.gz') or file_ext.endswith('.xml.gz')
        
        # Reset file pointer to beginning (important for file streams)
        await file.seek(0)
        
        # Create temporary file with appropriate suffix
        suffix = ".zip" if is_zip else ".xml.gz"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Extract and read XML content based on file type
            xml_content = None
            
            if is_zip:
                # Handle ZIP file
                try:
                    with zipfile.ZipFile(tmp_path, 'r') as zip_file:
                        # Look for XML files in the zip
                        xml_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                        if not xml_files:
                            # List all files in zip for debugging
                            all_files = zip_file.namelist()
                            raise HTTPException(
                                status_code=400, 
                                detail=f"ZIP file does not contain any XML files. Found files: {', '.join(all_files[:10])}"
                            )
                        # Use the first XML file found
                        print(f"[DEBUG] Extracting XML file '{xml_files[0]}' from ZIP archive")
                        xml_content = zip_file.read(xml_files[0])
                        if not xml_content:
                            raise HTTPException(
                                status_code=400,
                                detail=f"XML file '{xml_files[0]}' in ZIP is empty"
                            )
                        print(f"[DEBUG] Extracted {len(xml_content)} bytes from ZIP")
                except zipfile.BadZipFile as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid ZIP file. The file may be corrupted or not a valid ZIP archive: {str(e)}"
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error processing ZIP file: {str(e)}"
                    )
            elif is_gz:
                # Handle GZIP file
                try:
                    with gzip.open(tmp_path, 'rb') as gz_file:
                        xml_content = gz_file.read()
                except (gzip.BadGzipFile, OSError):
                    # If gzip fails, try reading as plain XML
                    with open(tmp_path, 'rb') as xml_file:
                        xml_content = xml_file.read()
            elif file_ext.endswith('.xml'):
                # Handle plain XML file
                with open(tmp_path, 'rb') as xml_file:
                    xml_content = xml_file.read()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please use .xml.gz, .gz, .zip, or .xml"
                )
            
            # Parse XML
            try:
                kpi_data = parse_ericsson_pm_xml(xml_content)
                print(f"[DEBUG] Parsed {len(kpi_data)} KPI records from XML")
                if kpi_data:
                    print(f"[DEBUG] Sample KPI: {kpi_data[0]}")
            except Exception as parse_error:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[DEBUG] XML parsing error: {error_trace}")
                # Provide more helpful error message
                error_msg = f"XML parsing failed: {str(parse_error)}. "
                error_msg += "The XML structure may not match expected Ericsson ENM PM format. "
                error_msg += "Please verify the file format."
                raise HTTPException(status_code=400, detail=error_msg)
            
            if not kpi_data:
                # Log XML structure for debugging
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_content)
                    root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                    print(f"[DEBUG] XML root tag: {root_tag}")
                    print(f"[DEBUG] XML has {len(list(root.iter()))} total elements")
                    # Log first few element tags
                    tags = [elem.tag.split('}')[-1] for elem in list(root.iter())[:10]]
                    print(f"[DEBUG] Sample tags: {tags}")
                except:
                    pass
                raise HTTPException(
                    status_code=400, 
                    detail="No KPI data found in XML file. The XML structure may not match the expected format. "
                           "Please check that the file contains PM measurement data in Ericsson ENM format. "
                           "Check backend console for debug details."
                )
            
            # Run deterministic RCA analysis with latest multi-module context
            rca_result = analyze_rca(
                kpi_data,
                alarm_summary=LATEST_ALARM_SUMMARY,
                backhaul_summary=LATEST_BACKHAUL_SUMMARY,
                attach_summary=LATEST_ATTACH_SUMMARY,
            )

            # Cache latest RCA for downstream features (e.g., PDF reports)
            global LATEST_RCA_RESULT
            LATEST_RCA_RESULT = rca_result
            
            # AI Feature B: Anomaly Detection
            anomaly_result = {}
            try:
                kpi_df = prepare_hourly_data(kpi_data)
                if not kpi_df.empty:
                    anomaly_result = detect_anomalies(kpi_df)
            except Exception as e:
                # Continue if anomaly detection fails
                print(f"Anomaly detection error: {e}")
                anomaly_result = {"error": str(e)}
            
            # AI Feature C: Drift Detection
            drift_result = {}
            try:
                # Extract site ID from KPI data
                site_id = None
                if kpi_data:
                    site_id = kpi_data[0].get("site", "default")
                drift_result = detect_drift(kpi_data, site_id=site_id)
            except Exception as e:
                # Continue if drift detection fails
                print(f"Drift detection error: {e}")
                drift_result = {"error": str(e)}
            
            # AI Feature A: Generate AI Summary
            ai_summary_text = ""
            try:
                ai_summary_text = generate_ai_summary(
                    kpi_data,
                    rca_result,
                    anomaly_result,
                    drift_result,
                    use_local=True
                )
            except Exception as e:
                # Continue if AI summary fails
                print(f"AI summary error: {e}")
                ai_summary_text = "AI summary unavailable"
            
            return RCAResponse(
                root_cause=rca_result["root_cause"],
                severity=rca_result["severity"],
                evidence=rca_result["evidence"],
                anomalies=rca_result["anomalies"],
                recommendations=rca_result["recommendations"],
                kpi_data=kpi_data,
                ai_summary=ai_summary_text,
                anomaly_detection=anomaly_result,
                drift=drift_result
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except gzip.BadGzipFile:
        raise HTTPException(status_code=400, detail="Invalid gzip file. The file may be corrupted or not a valid gzip archive.")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file. The file may be corrupted or not a valid ZIP archive.")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Analysis error: {error_trace}")  # Log full traceback for debugging
        # Also write to a log file so we can inspect errors even when running under a process manager
        try:
            log_path = Path(__file__).parent / "analysis_error.log"
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"\n=== {datetime.now().isoformat()} ===\n")
                log_file.write(error_trace + "\n")
        except Exception:
            # Logging failures should not mask the original error
            pass
        # Return the actual error message so frontend can show it
        error_msg = str(e) if str(e) else "Unknown error during analysis"
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")


class AskAIRequestWithContext(BaseModel):
    question: str
    kpi_data: Optional[List[Dict[str, Any]]] = None
    rca_result: Optional[Dict[str, Any]] = None
    site: Optional[str] = None
    time_range: Optional[str] = None


@app.post("/incident-report")
async def incident_report(payload: Dict[str, Any]):
    """
    Generate an incident report PDF for the current RCA context.

    The payload may include explicit summaries; if omitted, the latest cached
    RCA and module summaries are used where available.
    """
    try:
        combined = {
            "siteId": payload.get("siteId"),
            "timestampRange": payload.get("timestampRange"),
            "rcaResult": payload.get("rcaResult") or LATEST_RCA_RESULT,
            "kpiSummary": payload.get("kpiSummary"),
            "alarmSummary": payload.get("alarmSummary") or LATEST_ALARM_SUMMARY,
            "backhaulSummary": payload.get("backhaulSummary") or LATEST_BACKHAUL_SUMMARY,
            "attachSummary": payload.get("attachSummary") or LATEST_ATTACH_SUMMARY,
        }
        pdf_bytes = generate_incident_report_pdf(combined)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="ran_copilot_incident_report.pdf"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate incident report: {str(e)}")


@app.post("/ask-ai", response_model=AskAIResponse)
async def ask_ai_question(request: AskAIRequestWithContext):
    """AI Feature D: Answer natural language questions about KPI data"""
    try:
        # Use provided KPI context or empty list
        kpi_context = request.kpi_data or []
        rca_result = request.rca_result
        
        # Check if cloud/LLM is enabled
        allow_cloud = os.getenv("ALLOW_CLOUD", "0") == "1"
        api_key = os.getenv("OPENAI_API_KEY", "")
        use_local = not (allow_cloud and api_key)  # Use local if cloud not enabled OR no API key
        
        # Log for debugging
        print(f"[Ask AI] ALLOW_CLOUD={os.getenv('ALLOW_CLOUD', 'not set')}, "
              f"has_api_key={bool(api_key)}, use_local={use_local}")
        
        # Answer the question
        result = answer_question(
            request.question,
            kpi_context,
            rca_result,
            use_local=use_local
        )
        
        return AskAIResponse(
            answer=result["answer"],
            confidence=result["confidence"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {str(e)}")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

