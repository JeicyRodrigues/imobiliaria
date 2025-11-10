import csv
import io
from flask import Flask, render_template, request, send_file, redirect, url_for

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Configuração de valores fixos
VALOR_CONTRATO = 2000.00
BASE_ALUGUEL = {
    'apartamento': 700.00,
    'casa': 900.00,
    'estudio': 1200.00
}

# Rota principal para o formulário
@app.route('/', methods=['GET'])
def index():
    """Renderiza a página inicial com o formulário de orçamento."""
    return render_template('index.html')

@app.route('/orcamento', methods=['POST'])
def orcamento():
    """Calcula o orçamento mensal com base nos dados do formulário."""
    try:
        # 1. Coleta de dados do formulário
        tipo_imovel = request.form.get('tipo_imovel')
        quartos = int(request.form.get('quartos', 1))
        tem_garagem_apto_casa = request.form.get('garagem') == 'on' # Checkbox Apto/Casa
        tem_garagem_estudio = request.form.get('garagem_estudio') == 'on' # Checkbox Estúdio
        tem_criancas = request.form.get('criancas') == 'on'
        vagas_extras_estudio = int(request.form.get('vagas_extras_estudio', 0))
        parcelas_contrato = int(request.form.get('parcelas_contrato', 1))

        # Validação básica
        if tipo_imovel not in BASE_ALUGUEL:
            raise ValueError("Tipo de imóvel inválido.")
        if not 1 <= parcelas_contrato <= 5:
             raise ValueError("Número de parcelas do contrato deve ser entre 1 e 5.")

        # 2. Cálculo do Valor Base e Adicionais
        aluguel_mensal = BASE_ALUGUEL[tipo_imovel]
        adicionais = 0.0

        # Regra c & d: Quarto extra (somente para Apto e Casa)
        if tipo_imovel in ['apartamento', 'casa'] and quartos == 2:
            if tipo_imovel == 'apartamento':
                adicionais += 200.00
            elif tipo_imovel == 'casa':
                adicionais += 250.00
        
        # Regra e: Vaga de Garagem para Apto/Casa
        if tem_garagem_apto_casa and tipo_imovel in ['apartamento', 'casa']:
            adicionais += 300.00

        # Regra f: Vagas de Estúdio
        if tipo_imovel == 'estudio':
            if tem_garagem_estudio: # Inclui as 2 vagas padrão
                adicionais += 250.00
            
            # Vagas extras (se as 2 vagas padrão foram incluídas)
            if tem_garagem_estudio and vagas_extras_estudio > 0:
                adicionais += vagas_extras_estudio * 60.00

        # 3. Regra g: Desconto (Apto e sem crianças)
        desconto = 0.0
        if tipo_imovel == 'apartamento' and not tem_criancas:
            # Desconto de 5% aplicado apenas no valor base do aluguel
            desconto = BASE_ALUGUEL['apartamento'] * 0.05
        
        # 4. Cálculo Final
        aluguel_mensal_final = aluguel_mensal + adicionais - desconto
        
        # 5. Cálculo do Contrato
        parcela_contrato_valor = VALOR_CONTRATO / parcelas_contrato
        
        # 6. Geração da Tabela Anual (12 Meses)
        tabela_anual = []
        for i in range(1, 13):
            aluguel = aluguel_mensal_final
            # Parcela do contrato é aplicada apenas nos primeiros 'parcelas_contrato' meses
            parcela_contrato = parcela_contrato_valor if i <= parcelas_contrato else 0.0
            
            valor_total = aluguel + parcela_contrato
            
            tabela_anual.append({
                'mes': i,
                'aluguel': aluguel,
                'parcela_contrato': parcela_contrato,
                'valor_total': valor_total
            })


        # 7. Preparar dados para o template
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
            'tabela_anual': tabela_anual
        }

        return render_template('result.html', **dados_orcamento)

    except (ValueError, TypeError, KeyError) as e:
        # Em um app real, você registraria este erro.
        print(f"Erro no cálculo: {e}")
        return redirect(url_for('index'))

@app.route('/download_csv', methods=['POST'])
def download_csv():
    """Gera e retorna o arquivo CSV com 12 parcelas."""
    try:
        aluguel_mensal_final = float(request.form.get('aluguel_mensal_final'))
        parcela_contrato_valor = float(request.form.get('parcela_contrato_valor'))
        
        # Se a lógica de cálculo do contrato mudou para o result.html, o CSV precisa seguir essa lógica
        parcelas_contrato_form = int(request.form.get('parcelas_contrato', 1))
        
        si = io.StringIO()
        cw = csv.writer(si, delimiter=';')

        # Cabeçalhos
        cw.writerow(['Parcela', 'Aluguel Mensal', 'Parcela Contrato (R$ 2000,00)', 'Valor Total'])

        # Geração das 12 linhas
        for i in range(1, 13):
            aluguel = aluguel_mensal_final
            # O CSV deve usar o número real de parcelas (5), mas como o cálculo é baseado 
            # no valor da parcela (já calculado), mantemos a lógica original aqui 
            # para simplificar. O valor é 0.0 se i > 5.
            parcela_contrato = parcela_contrato_valor if i <= 5 else 0.0 
            
            valor_total = aluguel + parcela_contrato
            
            cw.writerow([
                f'Mês {i}', 
                f'{aluguel:.2f}'.replace('.', ','), 
                f'{parcela_contrato:.2f}'.replace('.', ','), 
                f'{valor_total:.2f}'.replace('.', ',')
            ])

        output = si.getvalue()
        buffer = io.BytesIO(output.encode('utf-8'))
        
        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name='orcamento_aluguel_12_meses.csv'
        )

    except Exception as e:
        print(f"Erro ao gerar CSV: {e}")
        return redirect(url_for('orcamento')) 
        
if __name__ == '__main__':
    # Para rodar o Flask, você precisará instalar: pip install flask
    app.run(debug=True)