import csv
import io
from flask import Flask, render_template, request, send_file, redirect, url_for


app = Flask(__name__)


VALOR_CONTRATO = 2000.00
BASE_ALUGUEL = {
    'apartamento': 700.00,
    'casa': 900.00,
    'estudio': 1200.00
}


@app.route('/', methods=['GET'])
def index():
    """Renderiza a página inicial com o formulário de orçamento."""
    return render_template('index.html')

@app.route('/orcamento', methods=['POST'])
def orcamento():
    """Calcula o orçamento mensal com base nos dados do formulário."""
    try:
        
        tipo_imovel = request.form.get('tipo_imovel')
        quartos = int(request.form.get('quartos', 1))
        tem_garagem_apto_casa = request.form.get('garagem') == 'on' 
        tem_garagem_estudio = request.form.get('garagem_estudio') == 'on' 
        tem_criancas = request.form.get('criancas') == 'on'
        vagas_extras_estudio = int(request.form.get('vagas_extras_estudio', 0))
        parcelas_contrato = int(request.form.get('parcelas_contrato', 1))

       
        if tipo_imovel not in BASE_ALUGUEL:
            raise ValueError("Tipo de imóvel inválido.")
        if not 1 <= parcelas_contrato <= 5:
             raise ValueError("Número de parcelas do contrato deve ser entre 1 e 5.")

       
        aluguel_mensal = BASE_ALUGUEL[tipo_imovel]
        adicionais = 0.0

       
        if tipo_imovel in ['apartamento', 'casa'] and quartos == 2:
            if tipo_imovel == 'apartamento':
                adicionais += 200.00
            elif tipo_imovel == 'casa':
                adicionais += 250.00
        
        
        if tem_garagem_apto_casa and tipo_imovel in ['apartamento', 'casa']:
            adicionais += 300.00

       
        if tipo_imovel == 'estudio':
            if tem_garagem_estudio: 
                adicionais += 250.00
            
           
            if tem_garagem_estudio and vagas_extras_estudio > 0:
                adicionais += vagas_extras_estudio * 60.00

       
        desconto = 0.0
        if tipo_imovel == 'apartamento' and not tem_criancas:
            
            desconto = BASE_ALUGUEL['apartamento'] * 0.05
        
        
        aluguel_mensal_final = aluguel_mensal + adicionais - desconto
        
      
        parcela_contrato_valor = VALOR_CONTRATO / parcelas_contrato
        
      
        tabela_anual = []
        for i in range(1, 13):
            aluguel = aluguel_mensal_final
            
            parcela_contrato = parcela_contrato_valor if i <= parcelas_contrato else 0.0
            
            valor_total = aluguel + parcela_contrato
            
            tabela_anual.append({
                'mes': i,
                'aluguel': aluguel,
                'parcela_contrato': parcela_contrato,
                'valor_total': valor_total
            })


     
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
        
        print(f"Erro no cálculo: {e}")
        return redirect(url_for('index'))

@app.route('/download_csv', methods=['POST'])
def download_csv():
    """Gera e retorna o arquivo CSV com 12 parcelas."""
    try:
        aluguel_mensal_final = float(request.form.get('aluguel_mensal_final'))
        parcela_contrato_valor = float(request.form.get('parcela_contrato_valor'))
        
       
        parcelas_contrato_form = int(request.form.get('parcelas_contrato', 1))
        
        si = io.StringIO()
        cw = csv.writer(si, delimiter=';')

     
        cw.writerow(['Parcela', 'Aluguel Mensal', 'Parcela Contrato (R$ 2000,00)', 'Valor Total'])

    
        for i in range(1, 13):
            aluguel = aluguel_mensal_final
           
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
    
    app.run(debug=True)