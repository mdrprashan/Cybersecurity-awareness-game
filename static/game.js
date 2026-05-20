document.addEventListener("DOMContentLoaded", function () {
    const options = document.querySelectorAll(".form-check-input");

    options.forEach(function (option) {
        option.addEventListener("change", function () {
            options.forEach(function (item) {
                item.parentElement.classList.remove("bg-light");
            });

            option.parentElement.classList.add("bg-light");
        });
    });
});