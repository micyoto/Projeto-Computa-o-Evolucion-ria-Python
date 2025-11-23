import numpy as np
import random
import math

# --- FUNÇÕES OBJETIVO ---

def funcao_quadratica(x):
    """
    Função Quadrática (f1): f(x) = sum(x^2)
    Restrição: -10 <= x <= 10
    """
    return np.sum(x**2)

def funcao_rastrigin_restrita(x):
    """
    Função Rastrigin com Restrições (TP03).
    """
    nvar = len(x)
    # Função Objetivo
    f_val = 10 * nvar + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))
    
    # Cálculo de Penalidade (g(x) <= 0 e h(x) = 0)
    g = np.sin(2 * np.pi * x) + 0.5
    h = np.cos(2 * np.pi * x) + 0.5
    
    violations_g = np.sum(np.maximum(0, g)**2)
    violations_h = np.sum(h**2)
    
    penalidade = 1e9 * (violations_g + violations_h)
    return f_val + penalidade

# --- CLASSE ALGORITMO GENÉTICO (Mantida igual, padrão Professor) ---

class AlgoritmoGenetico:
    def __init__(self, nvar, limites, params):
        self.nvar = nvar
        self.xmin, self.xmax = limites
        self.params = params
        self.populacao = []
        self.fitness = []
        self.best_history = []
        
        # LÓGICA DO PROFESSOR
        self.n_pop = int(max(20, 4 * np.ceil(nvar / 2)))
        self.pmut = 1.0 / float(nvar)
        self.pcruz = params['AG_PROB_CRUZAMENTO']
        self.eta_cruz = params['AG_ETA_CRUZ']
        self.eta_mut = params['AG_ETA_MUT']
        self.elitismo = int(params['AG_ELITISMO'])

    def inicializar(self):
        self.populacao = np.random.uniform(self.xmin, self.xmax, (self.n_pop, self.nvar))
        
    def avaliar(self, func_obj):
        vals = [func_obj(ind) for ind in self.populacao]
        self.fitness = np.array(vals)

    def sbx_crossover(self, p1, p2):
        if random.random() > self.pcruz:
            return p1.copy(), p2.copy()
        
        c1, c2 = p1.copy(), p2.copy()
        for i in range(self.nvar):
            if random.random() <= 0.5 and abs(p1[i] - p2[i]) > 1e-14:
                y1, y2 = min(p1[i], p2[i]), max(p1[i], p2[i])
                delta = y2 - y1
                rand = random.random()
                
                beta = 1.0 + (2.0 * (y1 - self.xmin) / delta)
                alpha = 2.0 - beta ** -(self.eta_cruz + 1.0)
                if rand <= (1.0 / alpha):
                    betaq = (rand * alpha) ** (1.0 / (self.eta_cruz + 1.0))
                else:
                    betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (self.eta_cruz + 1.0))
                
                c1[i] = 0.5 * (y1 + y2 - betaq * delta)

                beta = 1.0 + (2.0 * (self.xmax - y2) / delta)
                alpha = 2.0 - beta ** -(self.eta_cruz + 1.0)
                if rand <= (1.0 / alpha):
                    betaq = (rand * alpha) ** (1.0 / (self.eta_cruz + 1.0))
                else:
                    betaq = (1.0 / (2.0 - rand * alpha)) ** (1.0 / (self.eta_cruz + 1.0))
                
                c2[i] = 0.5 * (y1 + y2 + betaq * delta)
        
        return np.clip(c1, self.xmin, self.xmax), np.clip(c2, self.xmin, self.xmax)

    def polynomial_mutation(self, ind):
        mutant = ind.copy()
        for i in range(self.nvar):
            if random.random() <= self.pmut:
                y = mutant[i]
                yl, yu = self.xmin, self.xmax
                delta1 = (y - yl) / (yu - yl)
                delta2 = (yu - y) / (yu - yl)
                rand = random.random()
                mut_pow = 1.0 / (self.eta_mut + 1.0)
                
                if rand <= 0.5:
                    val = 2.0 * rand + (1.0 - 2.0 * rand) * (1.0 - delta1) ** (self.eta_mut + 1.0)
                    deltaq = val ** mut_pow - 1.0
                else:
                    val = 2.0 * (1.0 - rand) + 2.0 * (rand - 0.5) * (1.0 - delta2) ** (self.eta_mut + 1.0)
                    deltaq = 1.0 - val ** mut_pow
                
                mutant[i] = y + deltaq * (yu - yl)
        return np.clip(mutant, self.xmin, self.xmax)

    def executar(self, funcao_custo):
        self.inicializar()
        evals = 0
        limit_evals = self.params['N_AVALIACOES']
        self.avaliar(funcao_custo)
        evals += self.n_pop
        
        best_idx = np.argmin(self.fitness)
        self.best_history.append(self.fitness[best_idx])
        
        while evals < limit_evals:
            sorted_idx = np.argsort(self.fitness)
            elites = [self.populacao[i].copy() for i in sorted_idx[:self.elitismo]]
            
            parents = []
            for _ in range(self.n_pop):
                a, b = random.sample(range(self.n_pop), 2)
                parents.append(self.populacao[a] if self.fitness[a] < self.fitness[b] else self.populacao[b])
            
            new_pop = []
            while len(new_pop) < self.n_pop:
                p1 = random.choice(parents)
                p2 = random.choice(parents)
                c1, c2 = self.sbx_crossover(p1, p2)
                c1 = self.polynomial_mutation(c1)
                c2 = self.polynomial_mutation(c2)
                new_pop.extend([c1, c2])
            
            n_filhos_necessarios = self.n_pop - self.elitismo
            proxima_geracao = elites + new_pop[:n_filhos_necessarios]
            self.populacao = np.array(proxima_geracao)
            
            self.avaliar(funcao_custo)
            evals += n_filhos_necessarios
            self.best_history.append(np.min(self.fitness))
            
        best_final_idx = np.argmin(self.fitness)
        return self.populacao[best_final_idx], self.fitness[best_final_idx], self.best_history

# --- CLASSE EVOLUÇÃO DIFERENCIAL (Atualizada: DE/best/1/bin) ---

class EvolucaoDiferencial:
    def __init__(self, nvar, limites, params):
        self.nvar = nvar
        self.xmin, self.xmax = limites
        self.params = params
        self.populacao = []
        self.fitness = []
        self.best_history = []
        
    def inicializar(self):
        self.populacao = np.random.uniform(self.xmin, self.xmax, (self.params['N_POPULACAO'], self.nvar))
        
    def executar(self, funcao_custo):
        """
        Variante: DE/best/1/bin
        Vetor base = Melhor indivíduo da população atual.
        """
        self.inicializar()
        n_pop = self.params['N_POPULACAO']
        F = self.params['DE_F']
        CR = self.params['DE_CR']
        
        # Avaliação inicial
        self.fitness = np.array([funcao_custo(ind) for ind in self.populacao])
        evals = n_pop
        limit_evals = self.params['N_AVALIACOES']
        
        best_idx = np.argmin(self.fitness)
        self.best_history.append(self.fitness[best_idx])
        
        while evals < limit_evals:
            # Encontra o índice do MELHOR indivíduo da geração atual (Estratégia DE/best)
            idx_best = np.argmin(self.fitness)
            x_best = self.populacao[idx_best]
            
            nova_populacao = np.copy(self.populacao)
            
            for i in range(n_pop):
                # Sorteia r2 e r3 (que aqui chamaremos de r1 e r2 para simplificar a notação de código)
                # Eles devem ser diferentes de i
                indices = list(range(n_pop))
                indices.remove(i)
                
                # Sorteia 2 índices aleatórios
                r1, r2 = random.sample(indices, 2)
                
                x_r1 = self.populacao[r1]
                x_r2 = self.populacao[r2]
                
                # Mutação DE/best/1: v = x_best + F * (x_r1 - x_r2)
                vetor_ruido = x_best + F * (x_r1 - x_r2)
                
                # Crossover Binomial
                j_rand = random.randint(0, self.nvar - 1)
                vetor_teste = np.copy(self.populacao[i])
                
                for j in range(self.nvar):
                    if random.random() <= CR or j == j_rand:
                        vetor_teste[j] = vetor_ruido[j]
                
                # Garante limites
                vetor_teste = np.clip(vetor_teste, self.xmin, self.xmax)
                
                # Seleção Greedy
                fit_teste = funcao_custo(vetor_teste)
                evals += 1
                
                # Se o filho for melhor ou igual, substitui o pai
                if fit_teste <= self.fitness[i]:
                    nova_populacao[i] = vetor_teste
                    self.fitness[i] = fit_teste
                
                if evals >= limit_evals: break
            
            self.populacao = nova_populacao
            self.best_history.append(np.min(self.fitness))
            
        best_final_idx = np.argmin(self.fitness)
        return self.populacao[best_final_idx], self.fitness[best_final_idx], self.best_history