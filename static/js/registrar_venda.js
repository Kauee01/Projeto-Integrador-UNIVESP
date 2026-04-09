/**
 * registrar_venda.js — Lógica client-side da página de registro de vendas.
 *
 * Responsável por:
 * - Calcular subtotais por produto e total geral em tempo real
 * - Enviar os dados da venda para o backend via fetch (POST JSON)
 * - Redirecionar para a lista de vendas após sucesso
 */

document.addEventListener("DOMContentLoaded", function () {
    // Referência ao botão de registrar venda
    const btnRegistrar = document.getElementById("registrar-venda-btn");

    // Carrega o mapa de preços dos produtos (injetado no HTML via <script type="application/json">)
    const precos = JSON.parse(document.getElementById("dados-precos").textContent);

    /**
     * Recalcula o subtotal de cada produto e o total geral da venda.
     * Executado a cada alteração nos campos de quantidade.
     */
    function calcularTotal() {
        let totalGeral = 0;

        document.querySelectorAll(".quantidade-input").forEach(input => {
            const produtoId = input.getAttribute("data-produto-id");
            const quantidade = parseInt(input.value);
            const preco = precos[produtoId];

            if (!isNaN(quantidade) && quantidade > 0) {
                // Calcula e exibe o subtotal do produto
                const totalProduto = preco * quantidade;
                document.getElementById("total_" + produtoId).innerText = "R$ " + totalProduto.toFixed(2);
                totalGeral += totalProduto;
            } else {
                // Zera o subtotal se a quantidade for inválida ou zero
                document.getElementById("total_" + produtoId).innerText = "R$ 0.00";
            }
        });

        // Atualiza o total geral exibido na tela
        document.getElementById("total-geral").innerText = "Total: R$ " + totalGeral.toFixed(2);
    }

    // Vincula o recálculo a cada alteração nos campos de quantidade
    document.querySelectorAll(".quantidade-input").forEach(input => {
        input.addEventListener("input", calcularTotal);
    });

    /**
     * Evento de clique no botão "Registrar Venda".
     * Coleta os itens com quantidade > 0, valida os campos e envia via fetch POST.
     */
    btnRegistrar.addEventListener("click", async () => {
        const tipoPagamento = document.getElementById("tipo_pagamento").value;
        const itens = [];

        // Coleta apenas os produtos com quantidade maior que zero
        document.querySelectorAll(".quantidade-input").forEach(input => {
            const quantidade = parseInt(input.value);
            if (quantidade > 0) {
                itens.push({
                    produto_id: input.getAttribute("data-produto-id"),
                    quantidade: quantidade
                });
            }
        });

        // Validação: tipo de pagamento e pelo menos 1 item são obrigatórios
        if (!tipoPagamento || itens.length === 0) {
            alert("Preencha todos os campos corretamente!");
            return;
        }

        // Monta o payload JSON para o backend
        const dados = {
            tipo_pagamento_id: parseInt(tipoPagamento),
            itens: itens
        };

        try {
            // Envia a venda para o servidor
            const response = await fetch("/registrar-venda", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dados)
            });

            const resultado = await response.json();

            if (response.ok && resultado.success) {
                // Sucesso — redireciona para o histórico de vendas
                window.location.href = "/listar-vendas";
            } else {
                // Exibe o erro retornado pelo servidor
                alert(resultado.error || "Erro ao registrar a venda. Tente novamente.");
            }
        } catch (error) {
            // Erro de rede ou exceção no fetch
            alert("Erro ao registrar a venda. Tente novamente.");
        }
    });

    // Calcula o total inicial ao carregar a página
    calcularTotal();
});
