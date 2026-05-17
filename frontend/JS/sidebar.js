const menuBtn = document.getElementById("menu-btn");
const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();

    sidebar.classList.toggle("active");
    overlay.classList.toggle("active");
});

// cerrar con overlay
overlay.addEventListener("click", () => {
    sidebar.classList.remove("active");
    overlay.classList.remove("active");
});