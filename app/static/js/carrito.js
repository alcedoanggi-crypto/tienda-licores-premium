function actualizarBadgeCarrito(cantidad) {
  let badge = document.querySelector(".badge-carrito");
  const enlaceCarrito = document.querySelector('a[href$="/carrito/"]');
  if (cantidad > 0 && !badge && enlaceCarrito) {
    badge = document.createElement("span");
    badge.className = "badge-carrito ms-1";
    enlaceCarrito.appendChild(badge);
  }
  if (badge) {
    if (cantidad > 0) {
      badge.textContent = cantidad;
      badge.style.display = "inline-flex";
    } else {
      badge.remove();
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const formAgregar = document.getElementById("form-agregar-carrito");
  if (formAgregar) {
    formAgregar.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const productoId = formAgregar.dataset.productoId;
      const cantidad = formAgregar.querySelector('[name="cantidad"]').value;

      const datos = new FormData();
      datos.append("producto_id", productoId);
      datos.append("cantidad", cantidad);

      const boton = formAgregar.querySelector('button[type="submit"]');
      boton.disabled = true;

      try {
        const respuesta = await fetch("/carrito/agregar", { method: "POST", body: datos });
        const resultado = await respuesta.json();
        const mensajeDiv = document.getElementById("mensaje-carrito");

        if (resultado.ok) {
          mensajeDiv.className = "small mt-2 text-success";
          mensajeDiv.textContent = resultado.mensaje;
          actualizarBadgeCarrito(resultado.carrito_cantidad);
        } else {
          mensajeDiv.className = "small mt-2 text-danger";
          mensajeDiv.textContent = resultado.mensaje || "No se pudo agregar el producto.";
        }
      } finally {
        boton.disabled = false;
      }
    });
  }

  // Cantidad / eliminar en la página del carrito
  document.querySelectorAll(".input-cantidad-carrito").forEach((input) => {
    input.addEventListener("change", async () => {
      const datos = new FormData();
      datos.append("producto_id", input.dataset.productoId);
      datos.append("cantidad", input.value);
      const respuesta = await fetch("/carrito/actualizar", { method: "POST", body: datos });
      const resultado = await respuesta.json();
      if (resultado.ok) window.location.reload();
    });
  });

  document.querySelectorAll(".btn-quitar-carrito").forEach((boton) => {
    boton.addEventListener("click", async () => {
      const datos = new FormData();
      datos.append("producto_id", boton.dataset.productoId);
      const respuesta = await fetch("/carrito/eliminar", { method: "POST", body: datos });
      const resultado = await respuesta.json();
      if (resultado.ok) window.location.reload();
    });
  });
});
