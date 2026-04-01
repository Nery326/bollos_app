from django.urls import path
from .views import dashboard,nuevo_pedido,nueva_entrega,registrar_gasto,historial_entregas,nuevo_cliente,lista_clientes,editar_cliente,eliminar_cliente,cobrar_cliente,export_excel,reiniciar_datos,capital_base

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('nuevo_pedido/', nuevo_pedido, name='nuevo_pedido'),
    path('nueva_entrega/', nueva_entrega, name='nueva_entrega'),
    path('registrar_gasto/', registrar_gasto, name='registrar_gasto'),
    path('historial_entregas/', historial_entregas, name='historial_entregas'),
     path('capital_base/', capital_base, name='capital_base'),
    path('nuevo_cliente/', nuevo_cliente, name='nuevo_cliente'),
    path('clientes/', lista_clientes, name='lista_clientes'),
    path('clientes/cobrar/<int:cliente_id>/', cobrar_cliente, name='cobrar_cliente'),
    path('clientes/editar/<int:pk>/', editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', eliminar_cliente, name='eliminar_cliente'),
    path('export_excel/', export_excel, name='export_excel'),
    path('reiniciar_datos/',reiniciar_datos, name='reiniciar_datos'),
]
