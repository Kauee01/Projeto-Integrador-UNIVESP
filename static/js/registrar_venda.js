document.addEventListener("DOMContentLoaded", function () {
    const btnRegistrar = document.getElementById("registrar-venda-btn");

    // Carrega os preços dos produtos
    const precos = JSON.parse(document.getElementById("dados-precos").textContent);

    // Função para calcular o total por produto e o total geral
    function calcularTotal() {
        let totalGeral = 0;

        document.querySelectorAll(".quantidade-input").forEach(input => {
            const produtoId = input.getAttribute("data-produto-id");
            const quantidade = parseInt(input.value);
            const preco = precos[produtoId];

            if (!isNaN(quantidade) && quantidade > 0) {
                const totalProduto = preco * quantidade;
                document.getElementById("total_" + produtoId).innerText = "R$ " + totalProduto.toFixed(2);
                totalGeral += totalProduto;
            } else {
                document.getElementById("total_" + produtoId).innerText = "R$ 0.00";
            }
        });

        document.getElementById("total-geral").innerText = "Total: R$ " + totalGeral.toFixed(2);
    }

    // Evento de mudança de quantidade
    document.querySelectorAll(".quantidade-input").forEach(input => {
        input.addEventListener("input", calcularTotal);
    });

    // Ao clicar no botão "Registrar Venda"
    btnRegistrar.addEventListener("click", async () => {
        const tipoPagamento = document.getElementById("tipo_pagamento").value;
        const itens = [];

        document.querySelectorAll(".quantidade-input").forEach(input => {
            const quantidade = parseInt(input.value);
            if (quantidade > 0) {
                itens.push({
                    produto_id: input.getAttribute("data-produto-id"),
                    quantidade: quantidade
                });
            }
        });

        if (!tipoPagamento || itens.length === 0) {
            alert("Preencha todos os campos corretamente!");
            return;
        }

        const dados = {
            tipo_pagamento_id: parseInt(tipoPagamento),
            itens: itens
        };

        try {
            const response = await fetch("/registrar-venda", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(dados)
            });

            const resultado = await response.json();
            if (response.ok && resultado.success) {
                // Redireciona diretamente após sucesso
                window.location.href = "/listar-vendas";
            } else {
                alert(resultado.error || "Erro ao registrar a venda. Tente novamente.");
            }
        } catch (error) {
            alert("Erro ao registrar a venda. Tente novamente.");
        }
    });

    // Inicializar cálculo no carregamento
    calcularTotal();
});
