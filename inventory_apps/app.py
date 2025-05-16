from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Product, Location, ProductMovement
from datetime import datetime
from werkzeug.urls import quote 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        product_id = request.form['product_id']
        name = request.form['name']
        description = request.form['description']

        if Product.query.get(product_id):
            flash('Product ID already exists!', 'danger')
            return redirect(url_for('products'))

        new_product = Product(product_id=product_id, name=name, description=description)
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))

    products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=products)

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if ProductMovement.query.filter_by(product_id=product_id).first():
        flash('Cannot delete product with existing movements!', 'danger')
        return redirect(url_for('products'))

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/locations', methods=['GET', 'POST'])
def locations():
    if request.method == 'POST':
        location_id = request.form['location_id']
        name = request.form['name']
        address = request.form['address']

        if Location.query.get(location_id):
            flash('Location ID already exists!', 'danger')
            return redirect(url_for('locations'))

        new_location = Location(location_id=location_id, name=name, address=address)
        db.session.add(new_location)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('locations'))

    locations = Location.query.order_by(Location.name).all()
    return render_template('locations.html', locations=locations)

@app.route('/edit_location/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)

    if request.method == 'POST':
        location.name = request.form['name']
        location.address = request.form['address']
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations'))

    return render_template('edit_location.html', location=location)

@app.route('/delete_location/<location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)

    if (ProductMovement.query.filter_by(from_location=location_id).first() or 
        ProductMovement.query.filter_by(to_location=location_id).first()):
        flash('Cannot delete location with existing movements!', 'danger')
        return redirect(url_for('locations'))

    db.session.delete(location)
    db.session.commit()
    flash('Location deleted successfully!', 'success')
    return redirect(url_for('locations'))

@app.route('/movements', methods=['GET', 'POST'])
def movements():
    if request.method == 'POST':
        movement_id = request.form['movement_id']
        from_location = request.form['from_location'] if request.form['from_location'] != 'None' else None
        to_location = request.form['to_location'] if request.form['to_location'] != 'None' else None
        product_id = request.form['product_id']
        qty = int(request.form['qty'])

        if from_location == to_location:
            flash('Cannot move to the same location!', 'danger')
            return redirect(url_for('movements'))

        if qty <= 0:
            flash('Quantity must be positive!', 'danger')
            return redirect(url_for('movements'))

        if from_location:
            total_from = get_product_quantity(product_id, from_location)
            if total_from < qty:
                flash(f'Not enough quantity in source location. Available: {total_from}', 'danger')
                return redirect(url_for('movements'))

        if ProductMovement.query.get(movement_id):
            flash('Movement ID already exists!', 'danger')
            return redirect(url_for('movements'))

        new_movement = ProductMovement(
            movement_id=movement_id,
            from_location=from_location,
            to_location=to_location,
            product_id=product_id,
            qty=qty
        )
        db.session.add(new_movement)
        db.session.commit()
        flash('Movement added successfully!', 'success')
        return redirect(url_for('movements'))

    movements = ProductMovement.query.order_by(ProductMovement.timestamp.desc()).all()
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    return render_template('movements.html', movements=movements, products=products, locations=locations)

@app.route('/edit_movement/<movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)

    if request.method == 'POST':
        new_from = request.form['from_location'] if request.form['from_location'] != 'None' else None
        new_to = request.form['to_location'] if request.form['to_location'] != 'None' else None
        new_qty = int(request.form['qty'])

        if new_from == new_to:
            flash('Cannot move to the same location!', 'danger')
            return redirect(url_for('edit_movement', movement_id=movement_id))

        if new_qty <= 0:
            flash('Quantity must be positive!', 'danger')
            return redirect(url_for('edit_movement', movement_id=movement_id))

        old_from = movement.from_location
        old_qty = movement.qty
        product_id = movement.product_id

        if new_from:
            total_from = get_product_quantity(product_id, new_from)
            available = total_from + old_qty if new_from == old_from else total_from

            if available < new_qty:
                flash(f'Not enough quantity in source location. Available: {available}', 'danger')
                return redirect(url_for('edit_movement', movement_id=movement_id))

        movement.from_location = new_from
        movement.to_location = new_to
        movement.qty = new_qty
        db.session.commit()
        flash('Movement updated successfully!', 'success')
        return redirect(url_for('movements'))

    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()
    return render_template('edit_movement.html', movement=movement, products=products, locations=locations)

@app.route('/delete_movement/<movement_id>', methods=['POST'])
def delete_movement(movement_id):
    movement = ProductMovement.query.get_or_404(movement_id)
    db.session.delete(movement)
    db.session.commit()
    flash('Movement deleted successfully!', 'success')
    return redirect(url_for('movements'))

@app.route('/report')
def report():
    products = Product.query.order_by(Product.name).all()
    locations = Location.query.order_by(Location.name).all()

    report_data = []
    for product in products:
        for location in locations:
            qty = get_product_quantity(product.product_id, location.location_id)
            if qty > 0:
                report_data.append({
                    'product': product.name,
                    'location': location.name,
                    'qty': qty
                })

    return render_template('report.html', report_data=report_data)

def get_product_quantity(product_id, location_id):
    total_in = db.session.query(db.func.sum(ProductMovement.qty)).filter(
        ProductMovement.product_id == product_id,
        ProductMovement.to_location == location_id
    ).scalar() or 0

    total_out = db.session.query(db.func.sum(ProductMovement.qty)).filter(
        ProductMovement.product_id == product_id,
        ProductMovement.from_location == location_id
    ).scalar() or 0

    return total_in - total_out

if __name__ == '__main__':
    app.run(debug=True)
