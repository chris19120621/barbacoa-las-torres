from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import secrets
import os
import json
from datetime import date, timedelta
from flask import session, abort
from mysql.connector import Error
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

def db():
    return mysql.connector.connect(host=os.environ.get('DB_HOST','localhost'), user=os.environ.get('DB_USER','root'), password=os.environ.get('DB_PASSWORD',''), database=os.environ.get('DB_NAME','las_torres'))

def query(sql, args=(), one=False):
    conn = db()
    try:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, args)
            return cur.fetchone() if one else cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()

def execute(sql, args):
    conn = db()
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql, args)
            conn.commit()
        finally:
            cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



@app.context_processor
def csrf_context():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return {'csrf_token': session['csrf_token']}

def comprobar_csrf():
    if not secrets.compare_digest(request.form.get('csrf_token',''), session.get('csrf_token','')):
        abort(400, description='Formulario inválido. Recarga la página.')

def validar_producto(form):
    nombre = form.get('nombre','').strip()
    descripcion = form.get('descripcion','').strip()
    precio = Decimal(form.get('precio',''))
    costo = Decimal(form.get('costo',''))
    stock = int(form.get('stock',''))
    stock_minimo = int(form.get('stock_minimo','5'))
    if not nombre or len(nombre)>100 or len(descripcion)>255 or not precio.is_finite() or not costo.is_finite() or precio<0 or costo<0 or precio>99999999 or costo>99999999 or stock<0 or stock_minimo<0 or stock>10000000 or stock_minimo>10000000:
        raise ValueError('Revisa nombre, descripción, precios y existencias.')
    if precio.as_tuple().exponent < -2 or costo.as_tuple().exponent < -2:
        raise ValueError('Los precios admiten máximo dos decimales.')
    return (nombre, descripcion, precio, costo, stock, stock_minimo)

@app.route('/gestion-productos')
def gestion_productos():
    return render_template('gestion_productos.html', active='gestion', productos=query('SELECT * FROM productos ORDER BY id_producto DESC'))

@app.route('/gestion-productos/crear', methods=['POST'])
def crear_producto():
    comprobar_csrf()
    try:
        valores = validar_producto(request.form)
        empresa = query("SELECT id_empresa FROM empresas WHERE nombre=%s LIMIT 1", ('Barbacoa Las Torres',), one=True)
        if not empresa: raise ValueError('Importa la base de datos las_torres.sql.')
        execute('INSERT INTO productos(nombre,descripcion,precio,costo,stock,stock_minimo,id_empresa) VALUES (%s,%s,%s,%s,%s,%s,%s)', valores+(empresa['id_empresa'],))
        flash('Producto registrado correctamente.', 'success')
    except (ValueError, ArithmeticError, Error) as e:
        flash('No se pudo registrar el producto: '+str(e), 'danger')
    return redirect(url_for('gestion_productos'))

@app.route('/gestion-productos/<int:id_producto>/editar', methods=['POST'])
def editar_producto(id_producto):
    comprobar_csrf()
    try:
        valores = validar_producto(request.form)
        execute('UPDATE productos SET nombre=%s, descripcion=%s, precio=%s, costo=%s, stock=%s, stock_minimo=%s WHERE id_producto=%s', valores+(id_producto,))
        flash('Producto actualizado correctamente.', 'success')
    except (ValueError, ArithmeticError, Error) as e:
        flash('No se pudo actualizar: '+str(e), 'danger')
    return redirect(url_for('gestion_productos'))

@app.route('/gestion-productos/<int:id_producto>/eliminar', methods=['POST'])
def eliminar_producto(id_producto):
    comprobar_csrf()
    try:
      
        referencias=query('SELECT (SELECT COUNT(*) FROM detalle_ventas WHERE id_producto=%s) AS ventas, (SELECT COUNT(*) FROM movimientos_inventario WHERE id_producto=%s) AS movimientos', (id_producto,id_producto), one=True)
        if referencias['ventas'] or referencias['movimientos']:
            flash('No se puede eliminar: el producto tiene historial de ventas o inventario. Conserva el registro para no perder información.', 'warning')
        else:
            execute('DELETE FROM productos WHERE id_producto=%s', (id_producto,))
            flash('Producto eliminado correctamente.', 'success')
    except Error as e:
        flash('No se pudo eliminar el producto: '+str(e), 'danger')
    return redirect(url_for('gestion_productos'))

@app.route('/')
def dashboard():
    productos = query('SELECT * FROM productos ORDER BY id_producto DESC')
    v = query('SELECT COALESCE(SUM(total),0) total FROM ventas', one=True)['total']
    g = query('SELECT COALESCE(SUM(monto),0) total FROM gastos', one=True)['total']
    c = query('SELECT COALESCE(SUM(cantidad*costo_unitario),0) total FROM detalle_ventas', one=True)['total']
    dias = query('SELECT DATE(fecha) dia, SUM(total) total FROM ventas GROUP BY DATE(fecha) ORDER BY dia DESC LIMIT 7')
    dias.reverse()
    return render_template('dashboard.html', active='dashboard', productos=productos, ventas=v, gastos=g, utilidad=v-c-g, inventario=sum(p['costo']*p['stock'] for p in productos), bajo=sum(p['stock']<=p['stock_minimo'] for p in productos), labels=[str(x['dia']) for x in dias], valores=[float(x['total']) for x in dias], top=query('SELECT p.nombre, SUM(d.cantidad) unidades FROM detalle_ventas d JOIN productos p ON p.id_producto=d.id_producto GROUP BY p.id_producto,p.nombre ORDER BY unidades DESC LIMIT 5'), ultimas=query('SELECT id_venta,fecha,total,metodo_pago FROM ventas ORDER BY id_venta DESC LIMIT 5'))

@app.route('/productos')
def productos():
    return render_template('productos.html', active='productos', productos=query('SELECT * FROM productos ORDER BY id_producto DESC'))

@app.route('/inventario')
def inventario():
    return render_template('inventario.html', active='inventario', productos=query('SELECT * FROM productos ORDER BY nombre'), movimientos=query('SELECT m.fecha,m.tipo,m.cantidad,p.nombre FROM movimientos_inventario m JOIN productos p ON p.id_producto=m.id_producto ORDER BY m.id_movimiento DESC LIMIT 12'))

@app.route('/finanzas')
def finanzas():
    ventas = query('SELECT COALESCE(SUM(total),0) total FROM ventas',one=True)['total']
    costos = query('SELECT COALESCE(SUM(cantidad*costo_unitario),0) total FROM detalle_ventas',one=True)['total']
    gastos = query('SELECT COALESCE(SUM(monto),0) total FROM gastos',one=True)['total']
    return render_template('finanzas.html', active='finanzas', ventas=ventas, costos=costos, gastos=gastos, utilidad=ventas-costos-gastos, lista=query('SELECT * FROM gastos ORDER BY fecha DESC LIMIT 20'), hoy=date.today().isoformat())

def negocio_ids(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id_empresa FROM empresas ORDER BY id_empresa LIMIT 1")
    emp = cur.fetchone()
    if not emp:
        raise ValueError('Importa la base de datos las_torres.sql.')
    cur.execute('SELECT id_usuario FROM usuarios WHERE id_empresa=%s ORDER BY id_usuario LIMIT 1', (emp['id_empresa'],))
    usr = cur.fetchone()
    cur.close()
    if not usr:
        raise ValueError('Falta el usuario de caja en la base de datos.')
    return emp['id_empresa'], usr['id_usuario']

@app.route('/gastos/nuevo', methods=['POST'])
def nuevo_gasto():
    comprobar_csrf()
    try:
        concepto = request.form.get('concepto','').strip()
        categoria = request.form.get('categoria','Otros').strip()[:80]
        monto = Decimal(request.form.get('monto',''))
        fecha = request.form.get('fecha','')
        date.fromisoformat(fecha)
        if not concepto or len(concepto)>150 or not monto.is_finite() or monto<=0 or monto>999999999 or monto.as_tuple().exponent < -2:
            raise ValueError('Revisa el concepto, monto y fecha.')
        conn = db()
        try:
            empresa, _ = negocio_ids(conn)
            cur=conn.cursor()
            cur.execute('INSERT INTO gastos(id_empresa,concepto,categoria,monto,fecha) VALUES (%s,%s,%s,%s,%s)', (empresa,concepto,categoria,monto,fecha))
            conn.commit()
            cur.close()
        finally: conn.close()
        flash('Gasto registrado correctamente.','success')
    except (ValueError, ArithmeticError, Error) as exc:
        flash('No se pudo registrar el gasto: '+str(exc),'danger')
    return redirect(url_for('finanzas'))

@app.route('/punto-de-venta')
def punto_de_venta():
    return render_template('pos.html', active='pos', productos=query('SELECT * FROM productos WHERE stock > 0 ORDER BY nombre'))

@app.route('/ventas/cobrar', methods=['POST'])
def cobrar():
    comprobar_csrf()
    conn = None
    try:
        carrito = json.loads(request.form.get('carrito','[]'))
        metodo = request.form.get('metodo_pago','')
        if metodo not in ('efectivo','tarjeta','transferencia') or not isinstance(carrito,list) or not 1<=len(carrito)<=100:
            raise ValueError('Carrito o método de pago inválido.')
        cantidades={}
        for item in carrito:
            if not isinstance(item,dict) or type(item.get('id')) is not int or type(item.get('cantidad')) is not int:
                raise ValueError('Producto o cantidad inválidos.')
            pid,qty=item['id'],item['cantidad']
            if pid<=0 or qty<=0 or qty>1000: raise ValueError('Cantidad inválida.')
            cantidades[pid]=cantidades.get(pid,0)+qty
            if cantidades[pid]>1000: raise ValueError('Cantidad excesiva.')
        conn=db(); conn.start_transaction()
        empresa, usuario=negocio_ids(conn)
        cur=conn.cursor(dictionary=True)
        lineas=[]; total=Decimal('0.00')
        for pid in sorted(cantidades):
            cur.execute('SELECT id_producto,id_empresa,nombre,precio,costo,stock FROM productos WHERE id_producto=%s FOR UPDATE',(pid,))
            prod=cur.fetchone(); qty=cantidades[pid]
            if not prod or prod['id_empresa'] != empresa: raise ValueError('Producto no disponible para esta empresa.')
            if prod['stock']<qty: raise ValueError('Inventario insuficiente para '+prod['nombre'])
            subtotal=prod['precio']*qty
            total+=subtotal
            lineas.append((prod,qty,subtotal))
        cur.execute('INSERT INTO ventas(id_empresa,id_usuario,total,metodo_pago) VALUES (%s,%s,%s,%s)',(empresa,usuario,total,metodo))
        venta_id=cur.lastrowid
        for prod,qty,subtotal in lineas:
            cur.execute('INSERT INTO detalle_ventas(id_venta,id_producto,cantidad,precio_unitario,costo_unitario,subtotal) VALUES (%s,%s,%s,%s,%s,%s)',(venta_id,prod['id_producto'],qty,prod['precio'],prod['costo'],subtotal))
            cur.execute('UPDATE productos SET stock=stock-%s WHERE id_producto=%s',(qty,prod['id_producto']))
            cur.execute("INSERT INTO movimientos_inventario(id_empresa,id_producto,tipo,cantidad,motivo) VALUES (%s,%s,'salida',%s,%s)",(empresa,prod['id_producto'],qty,'Venta #'+str(venta_id)))
        conn.commit(); cur.close()
        flash(f'Venta #{venta_id} registrada. Total: ${total:,.2f}. Inventario actualizado.','success')
    except (ValueError, ArithmeticError, Error, json.JSONDecodeError) as exc:
        if conn: conn.rollback()
        flash('No se pudo cobrar: '+str(exc),'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('punto_de_venta'))

@app.route('/inventario/entrada', methods=['POST'])
def entrada_inventario():
    comprobar_csrf()
    conn=None
    try:
        pid=int(request.form.get('id_producto','0'))
        cantidad=int(request.form.get('cantidad','0'))
        if pid<=0 or not 1<=cantidad<=100000: raise ValueError('Producto o cantidad inválida.')
        conn=db(); conn.start_transaction(); empresa,_=negocio_ids(conn)
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT id_empresa FROM productos WHERE id_producto=%s FOR UPDATE',(pid,))
        p=cur.fetchone()
        if not p or p['id_empresa']!=empresa: raise ValueError('Producto no pertenece a Barbacoa Las Torres.')
        cur.execute('UPDATE productos SET stock=stock+%s WHERE id_producto=%s',(cantidad,pid))
        cur.execute("INSERT INTO movimientos_inventario(id_empresa,id_producto,tipo,cantidad,motivo) VALUES (%s,%s,'entrada',%s,'Reposición de inventario')",(empresa,pid,cantidad))
        conn.commit(); cur.close(); flash('Entrada registrada. Inventario actualizado.','success')
    except (ValueError,Error) as exc:
        if conn: conn.rollback()
        flash('No se pudo registrar la entrada: '+str(exc),'danger')
    finally:
        if conn: conn.close()
    return redirect(url_for('inventario'))

@app.route('/simulador')
def simulador():
    return render_template('simulador.html', active='simulador')

@app.route('/asistente')
def asistente():
    bajos=query('SELECT nombre,stock FROM productos WHERE stock <= stock_minimo')
    ventas=query('SELECT COALESCE(SUM(total),0) total FROM ventas',one=True)['total']
    costos=query('SELECT COALESCE(SUM(cantidad*costo_unitario),0) total FROM detalle_ventas',one=True)['total']
    gastos=query('SELECT COALESCE(SUM(monto),0) total FROM gastos',one=True)['total']
    top=query('SELECT p.nombre, SUM(d.cantidad) unidades FROM detalle_ventas d JOIN productos p ON p.id_producto=d.id_producto GROUP BY p.id_producto,p.nombre ORDER BY unidades DESC LIMIT 3')
    return render_template('asistente.html', active='asistente', bajos=bajos, ventas=ventas, utilidad=ventas-costos-gastos, top=top)

if __name__ == '__main__':
    app.run(debug=True)
