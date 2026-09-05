from datetime import datetime
import zoneinfo
from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult

class DateTimeTool(BaseTool):
    name = "datetime"
    description = "Get current date and time for a specific timezone"
    category = "utility"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The IANA timezone name, e.g. 'Asia/Tokyo' or 'America/New_York'. Default is 'UTC'."
                }
            }
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        tz_name = arguments.get("timezone", "UTC")
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
            current_time = datetime.now(tz)
            
            return ToolExecutionResult(
                success=True, 
                tool_name=self.name, 
                data={
                    "datetime": current_time.isoformat(),
                    "timezone": tz_name,
                    "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                }
            )
        except zoneinfo.ZoneInfoNotFoundError:
            return ToolExecutionResult(
                success=False, 
                tool_name=self.name, 
                error={"code": "INVALID_TIMEZONE", "message": f"Timezone '{tz_name}' not found."}
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False, 
                tool_name=self.name, 
                error={"code": "DATETIME_ERROR", "message": str(e)}
            )
