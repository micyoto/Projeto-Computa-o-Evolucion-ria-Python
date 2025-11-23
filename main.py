import numpy as np
import matplotlib.pyplot as plt
import algoritmos as alg
import time
import os

def ler_config(caminho='config.txt'):
    params = {}
    # Verifica explicitamente se o arquivo existe antes de abrir
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"O arquivo {caminho} não foi encontrado no diretório: {os.getcwd()}")

    with open(caminho, 'r') as f:
        for linha in f:
            # 1. Remove comentários inline (tudo que vier depois de um #)
            if '#' in linha:
                linha = linha.split('#')[0]
            
            linha = linha.strip()
            
            # 2. Pula linhas vazias ou que ficaram vazias após remover comentário
            if not linha: continue
            
            # 3. Processa chave: valor
            if ':' in linha:
                chave, valor = linha.split(':', 1)
                chave = chave.strip()
                valor = valor.strip()
                
                try:
                    # Tenta converter para float ou int
                    if '.' in valor:
                        params[chave] = float(valor)
                    else:
                        params[chave] = int(valor)
                except ValueError:
                    # Se falhar (ex: texto 'AMBAS'), mantém como string
                    params[chave] = valor
    return params

def rodar_experimento(AlgoritmoClass, nome_alg, funcao_obj, limites, params):
    n_execs = params['NUM_EXECUCOES']
    melhores_fitness = []
    historicos = []
    
    print(f"--> Iniciando {n_execs} execuções de {nome_alg}...")
    
    t_inicio = time.time()
    for i in range(n_execs):
        algo = AlgoritmoClass(params['N_VARIAVEIS'], limites, params)
        melhor_ind, melhor_fit, hist = algo.executar(funcao_obj)
        melhores_fitness.append(melhor_fit)
        historicos.append(hist)
        
    t_fim = time.time()
    print(f"    Concluído em {t_fim - t_inicio:.2f} segundos.")
    return np.array(melhores_fitness), historicos

def gerar_relatorios_e_graficos(dados_ag, dados_de, nome_func):
    fit_ag, hist_ag = dados_ag
    fit_de, hist_de = dados_de
    
    stats = f"\n=== RESULTADOS: {nome_func} ===\n"
    stats += f"{'Métrica':<15} | {'AG':<15} | {'DE':<15}\n"
    stats += "-"*50 + "\n"
    stats += f"{'Melhor':<15} | {np.min(fit_ag):<15.6f} | {np.min(fit_de):<15.6f}\n"
    stats += f"{'Pior':<15} | {np.max(fit_ag):<15.6f} | {np.max(fit_de):<15.6f}\n"
    stats += f"{'Média':<15} | {np.mean(fit_ag):<15.6f} | {np.mean(fit_de):<15.6f}\n"
    stats += f"{'Std Dev':<15} | {np.std(fit_ag):<15.6f} | {np.std(fit_de):<15.6f}\n"
    
    # Convergência
    min_len = min(min(len(h) for h in hist_ag), min(len(h) for h in hist_de))
    avg_hist_ag = np.mean([h[:min_len] for h in hist_ag], axis=0)
    avg_hist_de = np.mean([h[:min_len] for h in hist_de], axis=0)
    
    plt.figure(figsize=(10, 6))
    plt.plot(avg_hist_ag, label='AG (Média)', linestyle='--')
    plt.plot(avg_hist_de, label='DE (Média)', linewidth=2)
    plt.title(f'Convergência Média - {nome_func}')
    plt.xlabel('Gerações/Iterações')
    plt.ylabel('Fitness (Log Scale)')
    plt.yscale('log')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.savefig(f'grafico_convergencia_{nome_func}.png')
    plt.close()
    
    # Boxplot
    plt.figure(figsize=(8, 6))
    plt.boxplot([fit_ag, fit_de], labels=['AG', 'DE'])
    plt.title(f'Distribuição Final (40 Execuções) - {nome_func}')
    plt.ylabel('Fitness')
    plt.grid(True, alpha=0.3)
    plt.savefig(f'grafico_boxplot_{nome_func}.png')
    plt.close()
    
    return stats

if __name__ == "__main__":
    try:
        cfg = ler_config()
        print("Configuração lida com sucesso.")
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        exit()

    relatorio_final = "RELATÓRIO FINAL COMPARATIVO: AG vs DE\n" + "="*50 + "\n"
    
    cenarios = []
    if cfg['FUNCAO_ESCOLHIDA'] in ['QUADRATICA', 'AMBAS']:
        cenarios.append({'nome': 'Quadratica', 'func': alg.funcao_quadratica, 'limites': (-10, 10)})
    if cfg['FUNCAO_ESCOLHIDA'] in ['RASTRIGIN', 'AMBAS']:
        cenarios.append({'nome': 'Rastrigin_Restrita', 'func': alg.funcao_rastrigin_restrita, 'limites': (-5.12, 5.12)})

    for cenario in cenarios:
        print(f"\n>>> Processando Função: {cenario['nome']}")
        stats_ag = rodar_experimento(alg.AlgoritmoGenetico, "AG", cenario['func'], cenario['limites'], cfg)
        stats_de = rodar_experimento(alg.EvolucaoDiferencial, "DE", cenario['func'], cenario['limites'], cfg)
        
        texto_stats = gerar_relatorios_e_graficos(stats_ag, stats_de, cenario['nome'])
        print(texto_stats)
        relatorio_final += texto_stats + "\n"

    with open('relatorio_final.txt', 'w') as f:
        f.write(relatorio_final)
    print("\nProcesso finalizado! Verifique 'relatorio_final.txt' e os gráficos gerados.")