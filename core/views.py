import io
import xlsxwriter
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.db.models import Sum, F,FloatField
from .models import Cliente, Pedido, Entrega, Gasto,Capital
from django.utils.timezone import now
import json
from .forms import ClienteForm,CapitalForm
from django.contrib import messages
from django.db.models import Sum,F
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
import pandas as pd



def dashboard(request):
    # Total bollos pedidos
    total_bollos = Pedido.objects.aggregate(total=Sum('cantidad'))['total'] or 0

    # Bollos entregados pagados
    entregas_pagadas_qs = Entrega.objects.filter(pagado=True)
    entregas_pagadas = entregas_pagadas_qs.aggregate(total=Sum('cantidad_entregada'))['total'] or 0

    # Bollos pendientes por cobrar
    entregas_deben_qs = Entrega.objects.filter(pagado=False)
    entregas_deben = entregas_deben_qs.aggregate(total=Sum('cantidad_entregada'))['total'] or 0

    # Total ingresos y ganancia neta (solo entregas pagadas)
    total_ingresos = sum(e.cantidad_entregada * e.pedido.precio for e in entregas_pagadas_qs)
    total_gastos = Gasto.objects.aggregate(total=Sum('valor'))['total'] or 0
    ganancia_neta = total_ingresos - total_gastos

    # Bollos pendientes de entrega
    bollos_entregados = Entrega.objects.aggregate(total=Sum('cantidad_entregada'))['total'] or 0
    bollos_pendientes = total_bollos - bollos_entregados

    # CAPITAL ACTUAL: capital inicial + ingresos - gastos
    capital_inicial_obj = Capital.objects.order_by('-fecha').first()  # Último registro
    capital_inicial = capital_inicial_obj.monto_inicial if capital_inicial_obj else 0
    capital_actual = capital_inicial  - total_gastos

    # Datos para gráficas (últimos 30 días)
    from datetime import date, timedelta
    labels = []
    data_bollos = []
    data_ingresos = []

    for i in range(30, -1, -1):
        dia = date.today() - timedelta(days=i)
        pedidos_dia = Pedido.objects.filter(fecha=dia)
        bollos_dia = sum(p.cantidad for p in pedidos_dia)
        ingresos_dia = sum(
            sum(e.cantidad_entregada * e.pedido.precio for e in Entrega.objects.filter(pedido=p, pagado=True))
            for p in pedidos_dia
        )
        labels.append(dia.strftime("%d-%m"))
        data_bollos.append(bollos_dia)
        data_ingresos.append(ingresos_dia)

    context = {
        'total_bollos': total_bollos,
        'bollos_pendientes': bollos_pendientes,
        'entregas_pagadas': entregas_pagadas,
        'entregas_deben': entregas_deben,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'ganancia_neta': ganancia_neta,
        'capital_actual': capital_actual,
        'labels': labels,
        'data_bollos': data_bollos,
        'data_ingresos': data_ingresos,
    }

    return render(request, 'dashboard_bollos.html', context)

def nuevo_pedido(request):
    clientes = Cliente.objects.all()

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        cantidad = int(request.POST.get("cantidad", 0))

        cliente = Cliente.objects.get(id=cliente_id)
        precio = cliente.precio
        total = cantidad * precio

        Pedido.objects.create(
            cliente=cliente,
            cantidad=cantidad,
            precio=precio,
            total=total
        )

        messages.success(request, f"Pedido registrado: {cantidad} bollos para {cliente.nombre}, total ${total:.2f}")
        return redirect("nuevo_pedido")

    context = {
        "clientes": clientes
    }
    return render(request, "nuevo_pedido.html", context)

@login_required
def nueva_entrega(request):
    pedidos_raw = Pedido.objects.all().order_by('-fecha')
    pedidos = []

    for p in pedidos_raw:
        total_entregado = p.entrega_set.aggregate(total=Sum('cantidad_entregada'))['total'] or 0
        pedidos.append({
            'pedido': p,
            'total_entregado': total_entregado
        })

    if request.method == 'POST':
        pedido_id = request.POST.get('pedido')
        cantidad_entregada = int(request.POST.get('cantidad_entregada'))
        pagado = request.POST.get('pagado') == 'on'

        pedido = Pedido.objects.get(id=pedido_id)
        total_entregado = pedido.entrega_set.aggregate(total=Sum('cantidad_entregada'))['total'] or 0

        if total_entregado + cantidad_entregada > pedido.cantidad:
            messages.error(request, f"No se puede entregar más de lo pedido. Pedido: {pedido.cantidad}, Entregado hasta ahora: {total_entregado}")
        else:
            Entrega.objects.create(
                pedido=pedido,
                cantidad_entregada=cantidad_entregada,
                pagado=pagado
            )
            messages.success(request, f"Entrega registrada correctamente: {cantidad_entregada} bollos para {pedido.cliente.nombre}")
            return redirect('nueva_entrega')

    context = {
        'pedidos': pedidos
    }
    return render(request, 'nueva_entrega.html', context)

@login_required
def registrar_gasto(request):
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        valor = request.POST.get('valor')

        if not descripcion or not valor:
            messages.error(request, "Todos los campos son obligatorios.")
        else:
            try:
                valor = float(valor)
                gasto = Gasto.objects.create(descripcion=descripcion, valor=valor)
                messages.success(request, f"Gasto '{descripcion}' registrado correctamente: ${valor:.2f}")
                return redirect('registrar_gasto')
            except ValueError:
                messages.error(request, "El valor debe ser un número válido.")

    gastos = Gasto.objects.all().order_by('-fecha')
    context = {'gastos': gastos}
    return render(request, 'gasto_form.html', context)

def calcular_capital_actual():
    capital_base = Capital.objects.last().monto_inicial or 0

    total_gastos = Gasto.objects.aggregate(total=Sum('valor'))['total'] or 0
    total_ingresos = Pedido.objects.aggregate(total=Sum('total'))['total'] or 0

    capital_actual = capital_base  - total_gastos
    ganancia_neta = capital_base + total_ingresos - total_gastos

    return capital_actual, ganancia_neta

def historial_entregas(request):
    entregas = Entrega.objects.all().order_by('-fecha')

    # FILTRO POR FECHA
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        entregas = entregas.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        entregas = entregas.filter(fecha__lte=fecha_fin)

    # TOTAL DE BOLLOS ENTREGADOS Y PAGOS
    total_bollos = entregas.aggregate(total=Sum('cantidad_entregada'))['total'] or 0
    total_pagado = entregas.filter(pagado=True).aggregate(total=Sum('cantidad_entregada'))['total'] or 0

    context = {
        'entregas': entregas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_bollos': total_bollos,
        'total_pagado': total_pagado,
    }

    return render(request, 'historial_entregas.html', context)

def nuevo_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado correctamente')
            return redirect('dashboard')  # ruta a la lista de clientes
        else:
            messages.error(request, 'Por favor corrige los errores del formulario')
    else:
        form = ClienteForm()

    return render(request, 'nuevo_cliente.html', {'form': form})

def lista_clientes(request):
    clientes = Cliente.objects.all()

    # Para cada cliente, calculamos entregas pagadas y pendientes
    clientes_info = []
    for c in clientes:
        entregas_pagadas = Entrega.objects.filter(
            pedido__cliente=c, pagado=True
        ).aggregate(total=Sum('cantidad_entregada'))['total'] or 0

        entregas_pendientes = Entrega.objects.filter(
            pedido__cliente=c, pagado=False
        ).aggregate(total=Sum('cantidad_entregada'))['total'] or 0

        clientes_info.append({
            'cliente': c,
            'pagadas': entregas_pagadas,
            'pendientes': entregas_pendientes
        })

    return render(request, 'lista_clientes.html', {
        'clientes_info': clientes_info
    })

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente')
            return redirect('lista_clientes')
        else:
            messages.error(request, 'Corrige los errores del formulario')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'editar_cliente.html', {'form': form, 'cliente': cliente})

def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado correctamente')
        return redirect('lista_clientes')
    return render(request, 'eliminar_cliente.html', {'cliente': cliente})

def cobrar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    # Todas las entregas pendientes de pago
    entregas_pendientes = Entrega.objects.filter(
        pedido__cliente=cliente, pagado=False
    )

    if request.method == "POST":
        # Recibimos los IDs de entregas que se están pagando
        entregas_a_pagar = request.POST.getlist("entrega_id")
        for eid in entregas_a_pagar:
            entrega = Entrega.objects.get(pk=eid)
            entrega.pagado = True
            entrega.save()
        return redirect('lista_clientes')

    # Sumamos bollos pendientes y entregados
    total_entregados = Entrega.objects.filter(
        pedido__cliente=cliente, pagado=True
    ).aggregate(total=Sum('cantidad_entregada'))['total'] or 0

    total_pendientes = entregas_pendientes.aggregate(total=Sum('cantidad_entregada'))['total'] or 0

    return render(request, 'cobrar_cliente.html', {
        'cliente': cliente,
        'entregas_pendientes': entregas_pendientes,
        'total_entregados': total_entregados,
        'total_pendientes': total_pendientes
    })

def export_excel(request):
    # Crear un buffer en memoria
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    # Estilos
    header_format = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1})
    money_format = workbook.add_format({'num_format': '$#,##0.00', 'border': 1})
    text_format = workbook.add_format({'border': 1})
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    
    # HOJA 1: Pedidos
    ws1 = workbook.add_worksheet('Pedidos')
    ws1.write('A1', 'PEDIDOS VENDIDOS', title_format)
    headers_pedidos = ['ID', 'Cliente', 'Cantidad', 'Precio Unitario', 'Total', 'Fecha']
    for col_num, header in enumerate(headers_pedidos):
        ws1.write(2, col_num, header, header_format)

    pedidos = Pedido.objects.all().order_by('fecha')
    total_ventas = 0
    # En la sección de pedidos
    for row_num, pedido in enumerate(pedidos, start=3):
        ws1.write(row_num, 0, pedido.id, text_format)
        ws1.write(row_num, 1, str(pedido.cliente), text_format)  # <-- convertir a str
        ws1.write(row_num, 2, pedido.cantidad, text_format)
        ws1.write(row_num, 3, pedido.precio, money_format)
        ws1.write(row_num, 4, pedido.total, money_format)
        ws1.write(row_num, 5, str(pedido.fecha), text_format)
        total_ventas += pedido.total

    # Total ventas al final
    ws1.write(row_num + 2, 3, 'TOTAL VENTAS:', header_format)
    ws1.write(row_num + 2, 4, total_ventas, money_format)

    # HOJA 2: Gastos
    ws2 = workbook.add_worksheet('Gastos')
    ws2.write('A1', 'GASTOS', title_format)
    headers_gastos = ['ID', 'Descripción', 'Precio', 'Fecha']
    for col_num, header in enumerate(headers_gastos):
        ws2.write(2, col_num, header, header_format)

    gastos = Gasto.objects.all().order_by('fecha')
    total_gastos = 0
    for row_num, gasto in enumerate(gastos, start=3):
        ws2.write(row_num, 0, gasto.id, text_format)
        ws2.write(row_num, 1, getattr(gasto, 'descripcion', 'Gasto'), text_format)  # si tienes descripción
        ws2.write(row_num, 2, gasto.valor, money_format)
        ws2.write(row_num, 3, str(gasto.fecha), text_format)
        total_gastos += gasto.valor

    # Total gastos al final
    ws2.write(row_num + 2, 1, 'TOTAL GASTOS:', header_format)
    ws2.write(row_num + 2, 2, total_gastos, money_format)

    # HOJA 3: Resumen
    ws3 = workbook.add_worksheet('Resumen')
    ws3.write('A1', 'RESUMEN FINANCIERO', title_format)
    ws3.write('A3', 'Total Ventas', header_format)
    ws3.write('B3', total_ventas, money_format)
    ws3.write('A4', 'Total Gastos', header_format)
    ws3.write('B4', total_gastos, money_format)
    ws3.write('A5', 'Ganancia Neta', header_format)
    ws3.write('B5', total_ventas - total_gastos, money_format)
    ws3.write('A6', 'Capital Actual', header_format)
    # Si tienes un capital base, puedes sumarlo aquí
    capital_base = 0
    ws3.write('B6', capital_base + total_ventas - total_gastos, money_format)

    workbook.close()
    output.seek(0)

    # Crear respuesta HTTP
    filename = "resumen_ventas.xlsx"
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def reiniciar_datos(request):
    if request.method == 'POST':
        Pedido.objects.all().delete()
        Entrega.objects.all().delete()
        Gasto.objects.all().delete()
        # Retornamos JSON para la alerta en frontend
        return JsonResponse({'status': 'ok', 'mensaje': 'Los datos de ventas se han reiniciado correctamente.'})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido.'}, status=400)

def capital_base(request):
    capital = Capital.objects.first()  # obtenemos el capital existente si hay

    if request.method == "POST":
        form = CapitalForm(request.POST, instance=capital)
        if form.is_valid():
            form.save()
            if capital:
                messages.success(request, "Capital base actualizado correctamente.")
            else:
                messages.success(request, "Capital base registrado correctamente.")
            return redirect('capital_base')
    else:
        form = CapitalForm(instance=capital)

    return render(request, 'capital_base.html', {'form': form, 'capital': capital})
