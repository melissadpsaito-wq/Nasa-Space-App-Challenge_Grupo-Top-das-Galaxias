// Filtros do mapa: captura ano/mês/dia e envia ao backend Python via Fetch (POST JSON)
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-filtros');
    const selAno = document.getElementById('filtro-ano');
    const selMes = document.getElementById('filtro-mes');
    const inpDia = document.getElementById('filtro-dia');
    const status = document.getElementById('filtro-status');
    const botao = form.querySelector('button[type="submit"]');

    const ANO_MINIMO = 2000; // mantenha igual ao ANO_MINIMO do app.py
    const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];

    // Popula os selects (anos do mais recente ao mais antigo)
    const anoAtual = new Date().getFullYear();
    for (let a = anoAtual; a >= ANO_MINIMO; a--) selAno.add(new Option(a, a));
    MESES.forEach((nome, i) => selMes.add(new Option(nome, i + 1)));

    const mostrar = (texto, classe) => { status.textContent = texto; status.className = classe || ''; };

    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // não recarrega a página

        const filtros = {
            ano: Number(selAno.value),
            mes: Number(selMes.value),
            dia: inpDia.value === '' ? null : Number(inpDia.value) // dia é opcional
        };

        botao.disabled = true;
        mostrar('Aplicando filtros...');

        try {
            const resposta = await fetch('/api/focos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filtros)
            });
            const resultado = await resposta.json();

            if (!resposta.ok) throw new Error(resultado.message || 'Erro ao aplicar filtros.');

            mostrar(resultado.message, 'ok');
            console.log('Resposta do backend:', resultado);
            // PRÓXIMO PASSO: chamar limparHexagonos() e desenharHexagonoH3(...) (mapa_cores.js)
            // com os dados que o backend passar a devolver.
        } catch (erro) {
            mostrar(erro.message, 'erro');
        } finally {
            botao.disabled = false;
        }
    });
});
