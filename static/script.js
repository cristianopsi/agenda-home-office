document.querySelectorAll(".dia").forEach(dia => {
    dia.addEventListener("click", () => {
        const data = dia.dataset.data;
        if (!data) return;

        let atual = "";
        if (dia.classList.contains("home")) atual = "HOME";
        if (dia.classList.contains("presencial")) atual = "PRESENCIAL";

        let nova = prompt(
            "Digite:\nHOME\nPRESENCIAL\nou deixe vazio para limpar",
            atual
        );

        if (nova === null) return;
        nova = nova.toUpperCase();
        if (nova !== "HOME" && nova !== "PRESENCIAL") nova = null;

        fetch("/editar-dia", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({data, modalidade: nova})
        }).then(() => location.reload());
    });
});
