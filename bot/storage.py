import sqlite3
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .analysis.smc_engine_final import SMCAnalysisFinal

logger = logging.getLogger(__name__)

class BotStorage:
    """SQLite storage for bot data."""
    
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    default_symbol TEXT NOT NULL DEFAULT 'EUR_USD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    decision TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    bias TEXT NOT NULL,
                    result_data TEXT NOT NULL,  -- JSON serialized SignalResult
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_preferences (user_id)
                )
            """)
            
            # Scheduled jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    user_id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    interval_minutes INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    async def set_user_symbol(self, user_id: int, symbol: str):
        """Set user's default symbol."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update user preference
                cursor.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, default_symbol, updated_at) 
                    VALUES (?, ?, ?)
                """, (user_id, symbol, datetime.utcnow()))
                
                conn.commit()
                logger.info(f"Set default symbol {symbol} for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to set user symbol: {e}")
            raise
    
    async def get_user_symbol(self, user_id: int) -> str:
        """Get user's default symbol."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT default_symbol FROM user_preferences WHERE user_id = ?",
                    (user_id,)
                )
                
                result = cursor.fetchone()
                return result[0] if result else "EUR_USD"
                
        except Exception as e:
            logger.error(f"Failed to get user symbol: {e}")
            return "EUR_USD"
    
    async def save_analysis(self, result: SMCAnalysisFinal):
        """Save analysis result."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Serialize result to JSON
                result_data = result.model_dump_json()
                
                cursor.execute("""
                    INSERT INTO analysis_results 
                    (user_id, symbol, timestamp, decision, confidence, bias, result_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    1,  # Single user bot - hardcoded user_id
                    result.symbol,
                    result.timestamp,
                    result.signal,
                    result.confidence,
                    result.direction,
                    result_data
                ))
                
                conn.commit()
                logger.info(f"Saved analysis for {result.symbol}: {result.signal}")
                
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            raise
    
    async def get_last_analysis(self, user_id: int = 1) -> Optional[SMCAnalysisFinal]:
        """Get last analysis result."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT result_data FROM analysis_results 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    result_data = json.loads(result[0])
                    return SMCAnalysisFinal(**result_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get last analysis: {e}")
            return None
    
    async def get_analysis_history(
        self, 
        user_id: int = 1, 
        limit: int = 10
    ) -> list[SMCAnalysisFinal]:
        """Get analysis history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT result_data FROM analysis_results 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                results = []
                for result in cursor.fetchall():
                    result_data = json.loads(result[0])
                    results.append(SMCAnalysisFinal(**result_data))
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []
    
    async def save_scheduled_job(
        self, 
        user_id: int, 
        symbol: str, 
        interval_minutes: int, 
        job_id: str
    ):
        """Save scheduled job info."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO scheduled_jobs 
                    (user_id, symbol, interval_minutes, job_id, updated_at) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, symbol, interval_minutes, job_id, datetime.utcnow()))
                
                conn.commit()
                logger.info(f"Saved scheduled job for user {user_id}: {symbol} every {interval_minutes}min")
                
        except Exception as e:
            logger.error(f"Failed to save scheduled job: {e}")
            raise
    
    async def get_scheduled_job(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get scheduled job info."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT symbol, interval_minutes, job_id 
                    FROM scheduled_jobs 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        "symbol": result[0],
                        "interval_minutes": result[1],
                        "job_id": result[2]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get scheduled job: {e}")
            return None
    
    async def remove_scheduled_job(self, user_id: int):
        """Remove scheduled job info."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM scheduled_jobs WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                logger.info(f"Removed scheduled job for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to remove scheduled job: {e}")
            raise
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old analysis data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
                
                cursor.execute("""
                    DELETE FROM analysis_results 
                    WHERE created_at < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} old analysis records")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
