from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    # PUBLIC_INTERFACE
    # Run the FastAPI app locally on port 3001 for preview.
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=3001, reload=True)
