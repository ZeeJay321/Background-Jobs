from fastapi import FastAPI
from routers import products, orders
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="E-commerce API")

app.include_router(products.router)
app.include_router(orders.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Welcome to E-Commerce Application 🚀"}
