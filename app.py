from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from lp import *

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


userInfo = None


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get('/cart', response_class=HTMLResponse)
async def cart(request: Request):
    if userInfo is None:
        return RedirectResponse(url='/')

    recommeded_nutrients = calculate_recommendations(
        age=userInfo.get('age'),
        days=userInfo.get('days'),
        height=userInfo.get('height'),
        weight=userInfo.get('weight'),
        gender=userInfo.get('gender'),
    )

    return templates.TemplateResponse("cart.html", {"request": request, "userInfo": userInfo, "recommeded_nutrients": recommeded_nutrients})


@app.post('/api/info')
async def info(request: Request):
    data = await request.json()
    global userInfo
    userInfo = data
    userInfo['allergies'] = [x.lower().strip() for x in userInfo['allergies']]
    return RedirectResponse(url='/cart')


@app.post('/api/nutrients', response_class=JSONResponse)
async def get_nutrients(request: Request):
    cart = await request.json()
    nutrients = get_cart_nutrients(cart['items'])
    return {'nutrients': nutrients}


@app.get('/api/products', response_class=JSONResponse)
async def get_products():
    products = get_all_products(userInfo['diet'], userInfo['allergies'])
    return {'products': products}


@app.post('/api/suggestions', response_class=JSONResponse)
async def suggestions(request: Request):
    cart = await request.json()
    desc, items = get_suggestions(cart['items'], userInfo)
    return {
        'desc': desc,
        'items': items
    }

