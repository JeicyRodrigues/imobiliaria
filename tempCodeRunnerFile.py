        # 5. Cálculo do Contrato
        parcela_contrato_valor = VALOR_CONTRATO / parcelas_contrato
        
        # 6. Preparar dados para o template
        dados_orcamento = {
            'tipo_imovel': tipo_imovel.capitalize(),
            'aluguel_mensal_bruto': aluguel_mensal,
            'valor_adicionais': adicionais,
            'valor_desconto': desconto,
            'aluguel_mensal_final': aluguel_mensal_final,
            'valor_contrato': VALOR_CONTRATO,
            'parcelas_contrato': parcelas_contrato,
            'parcela_contrato_valor': parcela_contrato_valor,
            'total_mensal_com_contrato': aluguel_mensal_final + parcela_contrato_valor,
            'tem_criancas': tem_criancas,
        }

        return render_template('result.html', **dados_orcamento)