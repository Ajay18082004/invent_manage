from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash  
db = SQLAlchemy()

class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    movements = db.relationship('ProductMovement', backref='product', lazy=True)

class Location(db.Model):
    location_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)

    from_movements = db.relationship('ProductMovement', foreign_keys='ProductMovement.from_location', backref='from_loc', lazy=True)
    to_movements = db.relationship('ProductMovement', foreign_keys='ProductMovement.to_location', backref='to_loc', lazy=True)

class ProductMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    
    