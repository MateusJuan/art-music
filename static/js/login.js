// Função para filtrar as partituras conforme a pesquisa
function filtrarPartituras() {
    const pesquisa = document.getElementById("campoPesquisa").value.toLowerCase();
    const partituras = document.querySelectorAll(".partitura-item");
    const sugestoes = document.getElementById("sugestoes");

    // Limpa as sugestões antigas
    sugestoes.innerHTML = '';

    partituras.forEach(function (partitura) {
        const nomeArquivo = partitura.querySelector('a').textContent.toLowerCase();

        // Se a partitura não corresponder à pesquisa, oculta-a
        if (nomeArquivo.includes(pesquisa)) {
            partitura.style.display = 'block';
        } else {
            partitura.style.display = 'none';
        }
    });
}

// Função para realizar a pesquisa completa
function pesquisar(event) {
    event.preventDefault();
    const pesquisa = document.getElementById("campoPesquisa").value;
    if (pesquisa) {
        const urlPartitura = "{{ url_for('static', filename='PDF_PARTITURAS/') }}" + encodeURIComponent(pesquisa);
        const link = document.createElement('a');
        link.href = urlPartitura;
        link.target = '_blank'; // Isso garante que o PDF será aberto em uma nova guia
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link); // Remove o link temporário após clicar
    }
}
