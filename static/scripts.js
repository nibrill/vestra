
function toggleMenu() {
    const sidebar = document.getElementById("sidebar");
    const icon = document.querySelector(".hamburger");

    // Abre y cierra el menú lateral
    sidebar.classList.toggle("open");

    // Cambia el icono de hamburguesa a X
    icon.classList.toggle("active");
}

document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        document.querySelectorAll(".flash").forEach(el => el.remove());
    }, 3000);
});



function toggleMenu() {
    const sidebar = document.getElementById("sidebar");
    const hamburger = document.querySelector(".hamburger");

    sidebar.classList.toggle("open");
    hamburger.classList.toggle("active");
}
