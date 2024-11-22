const partiturasPage = {
    selecionar: function(genre) {
        let conteudo = '';
        if (genre === 'todos') {
            document.getElementById("todos").style.backgroundColor = "#746b60";
            document.getElementById("todos").style.borderRadius = "15px";
            conteudo = `
                <h2>Todos os gêneros selecionados</h2>
                <p>Aqui vai o conteúdo de todos os gêneros que você selecionar.</p>
            `;
        } else if (genre === 'gospel') {
            document.getElementById("gospel").style.backgroundColor = "#746b60";
            document.getElementById("gospel").style.borderRadius = "15px";
            conteudo = `
                <h2>Gospel/Religioso</h2>
                <table>
                    <thead>
                        <tr>
                            <td>Banda/Grupo</td>
                            <td>QTD</td>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><a href="vocalLivre.html">Vocal Livre</a></td>
                            <td id='qtd_vL'></td>
                        </tr>
                        <tr>
                            <td><a href="novotom.html">Novo Tom</a></td>
                            <td id='qtd_nT'></td>
                        </tr>
                    </tbody>
                </table>
            `;
        } else if (genre === 'rock') {
            document.getElementById("rock").style.backgroundColor = "#746b60";
            document.getElementById("rock").style.borderRadius = "15px";
            conteudo = `
                <h2>Rock</h2>
                <p>Aqui está o conteúdo de músicas de rock que você selecionou.</p>
            `;
        }

        document.getElementById('conteudo-selecionado').innerHTML = conteudo;
    }
};
