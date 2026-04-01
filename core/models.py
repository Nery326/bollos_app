from django.db import models

# ========================
# CLIENTES
# ========================
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    precio = models.DecimalField(max_digits=6, decimal_places=2, default=2.50)  # precio por defecto

    def __str__(self):
        return self.nombre


# ========================
# PEDIDOS
# ========================
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.precio = self.cliente.precio
        self.total = self.cantidad * self.precio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente.nombre} - {self.cantidad} bollos"


# ========================
# ENTREGAS
# ========================
class Entrega(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    cantidad_entregada = models.IntegerField()
    pagado = models.BooleanField(default=False)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.pedido.cliente.nombre} - {self.cantidad_entregada} bollos"


# ========================
# GASTOS
# ========================
class Gasto(models.Model):
    descripcion = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.descripcion
    
class Capital(models.Model):
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Capital inicial: ${self.monto_inicial}"