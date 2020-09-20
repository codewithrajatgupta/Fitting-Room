from fastapi import FastAPI, Response, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import urllib.request
from glob import glob
from PIL import Image
import os
from io import BytesIO
import secrets
import json
import aiofiles
import uvicorn
from metadata import tags_metadata
from pymongo import MongoClient
import pymongo
from bson import json_util 
import json


#dictionary for users registered
user = {
    "vera":"swordfish"
}

security = HTTPBasic()

app = FastAPI(openapi_tags=tags_metadata,
    title="Virtual_tryOn",
    description="Client API to serve virtual tryon",
    version="1.0.1",
    docs_url="/documentation")

def getCurrentUserName(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username in user.keys():
        password = user.get(credentials.username)
        password_match = secrets.compare_digest(credentials.password,password)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
            headers={"WWW-Authenticate": "Basic"},
            )
    if not(password_match):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
            )
    return credentials.username

#mounting the file directory 
#app.mount("/static", StaticFiles(directory='static'), name="static")

#actual function defination for try_on
@app.get('/{vendor_id}/try',tags=["try_on"])
def try_on(vendor_id:str,sex: str='men', top='mtp1', bottom='mb1', target='mt1',username: str = Depends(getCurrentUserName)):

    try:    
        client = pymongo.MongoClient("mongodb+srv://ekkosign_dev:gWxQXIuWMVpQc1lG@veradotstyle.p8up2.gcp.mongodb.net/<dbname>?retryWrites=true&w=majority")
        db = client.get_database('tryon')
        data_top = db.products.find_one({"vendor_id":vendor_id,"gender":sex,"category":'tops','productId':top,"targetpose":target})
        data_bottom = db.products.find_one({"vendor_id":vendor_id,"gender":sex,"category":'bottoms','productId':bottom,"targetpose":target})
        data_target = db.models.find_one({'modelId':target})
        print(data_top)
        rendered = Image.open(urllib.request.urlopen(data_target['imageURL']['image']))
        target_arm_im = Image.open(urllib.request.urlopen(data_target['imageURL']['arm_mask']))        
        warped_bottom = Image.open(urllib.request.urlopen(data_bottom['imageURL']['warped_bottom']))
        warped_torso = Image.open(urllib.request.urlopen(data_top['imageURL']['warped_torso']))
        warped_arms = Image.open(urllib.request.urlopen(data_top['imageURL']['warped_arms']))
        rendered.thumbnail((600,600))
        target_arm_im.thumbnail((600,600))
        rendered.paste(warped_bottom, warped_bottom)
        rendered.paste(target_arm_im, target_arm_im)
        rendered.paste(warped_torso, warped_torso)
        rendered.paste(warped_arms, warped_arms)

        buffer = BytesIO()
        rendered.convert('RGB').save(buffer, 'JPEG', optimize=True,quality=90)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/jpeg")
    except Exception as e:
        print(e)

    

if __name__ =="__main__":
    uvicorn.run(app)

