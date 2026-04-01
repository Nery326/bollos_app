from django.contrib import admin
from .models import Cliente, Pedido, Entrega, Gasto,Capital

# =========================
# ADMIN DE CLIENTES
# =========================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion', 'precio')  # Mostrar campos existentes
    search_fields = ('nombre', 'telefono')  # Búsqueda rápida por nombre o teléfono

# =========================
# ADMIN DE PEDIDOS
# =========================
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'cantidad', 'precio', 'total', 'fecha')  # Campos visibles
    list_filter = ('fecha',)  # Filtro por fecha de pedido
    search_fields = ('cliente__nombre',)  # Buscar por nombre del cliente

# =========================
# ADMIN DE ENTREGAS
# =========================
@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'cantidad_entregada', 'pagado', 'fecha')
    list_filter = ('fecha', 'pagado')  # Filtrar por fecha o si se pagó
    search_fields = ('pedido__cliente__nombre',)  # Buscar por cliente del pedido

# =========================
# ADMIN DE GASTOS
# =========================
@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'valor', 'fecha')
    list_filter = ('fecha',)  # Filtrar por fecha
    search_fields = ('descripcion',)  # Buscar por descripción

# =========================
# ADMIN DE CAPITAL
# =========================
@admin.register(Capital)
class CapitalAdmin(admin.ModelAdmin):
    list_display = ('monto_inicial', 'fecha')
    list_filter = ('fecha',)  # Filtrar por fecha
    
