import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import serial
import serial.tools.list_ports

@dataclass
class CalibrationData:
    thresholds: Dict
    cluster_stats: Dict
    
    def __post_init__(self):
        self.thresholds = self.calculate_thresholds()
    
    def calculate_thresholds(self) -> Dict:
        preto = self.cluster_stats['preto']['media']
        branco = self.cluster_stats['branco']['media']  
        vazio = self.cluster_stats['vazio']['media']
        
        limiar_preto_branco = (preto + branco) / 2
        limiar_branco_vazio = (branco + vazio) / 2
        
        return {
            'preto_branco': limiar_preto_branco,
            'branco_vazio': limiar_branco_vazio,
            'cluster_preto': preto,
            'cluster_branco': branco,
            'cluster_vazio': vazio
        }

class Xadrez3x3RealInterface:
    def __init__(self):
        self.arduino_port = 'COM6'
        self.baud_rate = 115200
        self.ser = None
        self.connected = False
        self.connection_in_progress = False
        
        self.calibration_data = None
        self.dados_matriz = None
        self.dados_classificados = None
        self.tamanho = 3
        
        # Estado do tabuleiro 3x3 com peças específicas
        self.pecas_tabuleiro = self.get_posicao_inicial_pecas()
        self.estado_anterior = None
        self.vez_das_brancas = True
        self.mapa_linhas = None
        
        self.root = None
        self.setup_interface()
        self.connect_arduino()
        self.salvar_estado_atual()

    def get_posicao_inicial_pecas(self):
        return [
            ['A', 'B', 'C'],  # Brancas
            ['·', '·', '·'],  # Vazio
            ['a', 'b', 'c']   # Pretas
        ]

    def salvar_estado_atual(self):
        if self.pecas_tabuleiro is not None:
            self.estado_anterior = [linha[:] for linha in self.pecas_tabuleiro]

    def setup_interface(self):
        self.root = tk.Tk()
        self.root.title("Sistema Real 3x3 - Leitura LDR")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(1000, 800)
        
        # Container principal com scroll
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        content_frame = self.scrollable_frame
        
        # Título
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_label = ttk.Label(title_frame, text="Sistema Real 3x3 - Leitura de LDRs", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        # Status conexão
        connection_frame = ttk.LabelFrame(content_frame, text="Status da Conexão", padding=10)
        connection_frame.pack(fill=tk.X, pady=5)
        
        status_display = ttk.Frame(connection_frame)
        status_display.pack(fill=tk.X, pady=5)
        
        self.connection_status = ttk.Label(status_display, text="Desconectado", 
                                          foreground="red", font=("Arial", 12, "bold"))
        self.connection_status.pack(side=tk.LEFT)
        
        ttk.Button(status_display, text="Conectar", command=self.force_connection).pack(side=tk.RIGHT)
        ttk.Button(status_display, text="Listar Portas", command=self.listar_portas).pack(side=tk.RIGHT, padx=5)
        
        # Turno
        turno_frame = ttk.Frame(connection_frame)
        turno_frame.pack(fill=tk.X, pady=5)
        
        self.turno_label = ttk.Label(turno_frame, text="Vez das BRANCAS", font=("Arial", 12, "bold"), foreground="blue")
        self.turno_label.pack()
        
        # Controles
        controls_frame = ttk.LabelFrame(content_frame, text="Controles", padding=10)
        controls_frame.pack(fill=tk.X, pady=5)
        
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        self.calibrate_btn = ttk.Button(buttons_frame, text="Calibrar", 
                                       command=self.iniciar_calibracao, state=tk.DISABLED, width=12)
        self.calibrate_btn.grid(row=0, column=0, padx=3, pady=3)
        
        self.read_btn = ttk.Button(buttons_frame, text="Ler Tabuleiro", 
                                  command=self.solicitar_leitura, state=tk.DISABLED, width=12)
        self.read_btn.grid(row=0, column=1, padx=3, pady=3)
        
        self.reset_btn = ttk.Button(buttons_frame, text="Reset", 
                                   command=self.resetar_sistema, state=tk.DISABLED, width=12)
        self.reset_btn.grid(row=0, column=2, padx=3, pady=3)
        
        self.test_btn = ttk.Button(buttons_frame, text="Teste", 
                                  command=self.teste_comunicacao, state=tk.DISABLED, width=12)
        self.test_btn.grid(row=0, column=3, padx=3, pady=3)
        
        for i in range(4):
            buttons_frame.columnconfigure(i, weight=1)
        
        self.calibration_status = ttk.Label(controls_frame, text="Sistema não calibrado", 
                                          foreground="red", font=("Arial", 10))
        self.calibration_status.pack(pady=5)
        
        # Tabuleiros visuais
        boards_frame = ttk.LabelFrame(content_frame, text="Tabuleiro 3x3 - Leitura Real", padding=10)
        boards_frame.pack(fill=tk.X, pady=5)
        
        boards_container = ttk.Frame(boards_frame)
        boards_container.pack(fill=tk.X, expand=True)
        
        # Valores brutos
        raw_frame = ttk.Frame(boards_container)
        raw_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(raw_frame, text="Valores LDR (0-1023)", font=("Arial", 11, "bold")).pack()
        self.raw_canvas = tk.Canvas(raw_frame, width=250, height=250, bg='white', 
                                   highlightthickness=1, highlightbackground="blue")
        self.raw_canvas.pack(pady=5)
        
        # Classificação
        pieces_frame = ttk.Frame(boards_container)
        pieces_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(pieces_frame, text="Peças", font=("Arial", 11, "bold")).pack()
        self.pieces_canvas = tk.Canvas(pieces_frame, width=250, height=250, bg='white', 
                                      highlightthickness=1, highlightbackground="green")
        self.pieces_canvas.pack(pady=5)
        
        self.create_3x3_boards()
        
        # Legenda
        legend_frame = ttk.Frame(boards_frame)
        legend_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(legend_frame, text="Legenda Peças:", font=("Arial", 10, "bold")).pack()
        
        legend_pecas = ttk.Frame(legend_frame)
        legend_pecas.pack(fill=tk.X, pady=5)
        
        ttk.Label(legend_pecas, text="Brancas:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(legend_pecas, text="A=Rainha, B=Torre, C=Bispo", foreground="darkblue").grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(legend_pecas, text="Pretas:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(legend_pecas, text="a=rainha, b=torre, c=bispo", foreground="darkred").grid(row=1, column=1, sticky="w", padx=5)
        
        legend_pecas.columnconfigure(1, weight=1)
        
        # Log do Sistema
        log_frame = ttk.LabelFrame(content_frame, text="Log do Sistema", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container, height=12, wrap=tk.WORD, font=("Consolas", 9))
        
        v_scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        h_scrollbar = ttk.Scrollbar(log_container, orient=tk.HORIZONTAL, command=self.log_text.xview)
        
        self.log_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(log_controls, text="Limpar Log", command=self.limpar_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Debug Sistema", command=self.debug_sistema).pack(side=tk.LEFT, padx=5)

    def create_3x3_boards(self):
        self.raw_labels = []
        self.piece_labels = []
        
        cell_size = 70
        margin = 20
        
        self.raw_canvas.delete("all")
        self.pieces_canvas.delete("all")
        
        for i in range(3):
            row_raw = []
            row_pieces = []
            for j in range(3):
                x1 = margin + j * cell_size
                y1 = margin + i * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                color = "#F0D9B5" if (i + j) % 2 == 0 else "#B58863"
                
                self.raw_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", width=1)
                label_raw = self.raw_canvas.create_text(x1 + cell_size/2, y1 + cell_size/2, 
                                                      text="---", font=("Arial", 10))
                row_raw.append(label_raw)
                
                self.pieces_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", width=1)
                label_piece = self.pieces_canvas.create_text(x1 + cell_size/2, y1 + cell_size/2, 
                                                           text="?", font=("Arial", 14, "bold"))
                row_pieces.append(label_piece)
            
            self.raw_labels.append(row_raw)
            self.piece_labels.append(row_pieces)

    def update_board_displays(self):
        try:
            if self.dados_matriz is not None:
                for i in range(3):
                    for j in range(3):
                        valor = self.dados_matriz[i, j]
                        self.raw_canvas.itemconfig(self.raw_labels[i][j], text=str(valor))
            
            for i in range(3):
                for j in range(3):
                    peca = self.pecas_tabuleiro[i][j]
                    
                    cor = "black"
                    if peca in ['A', 'B', 'C']:  # Brancas
                        cor = "blue"
                    elif peca in ['a', 'b', 'c']:  # Pretas
                        cor = "red"
                    elif peca == '·':  # Casa vazia
                        cor = "gray"
                    
                    self.pieces_canvas.itemconfig(self.piece_labels[i][j], text=peca, fill=cor)
            
            turno_text = "Vez das BRANCAS" if self.vez_das_brancas else "Vez das PRETAS"
            self.turno_label.config(text=turno_text)
            
            self.root.update_idletasks()
            
        except Exception as e:
            self.log_message(f"Erro ao atualizar displays: {e}")

    def classificar_casa(self, valor: int) -> int:
        if not self.calibration_data:
            return 0
        
        thresholds = self.calibration_data.thresholds
        
        if valor < thresholds['preto_branco']:
            return 2  # Preto (faixa baixa)
        elif valor < thresholds['branco_vazio']:
            return 1  # Branco (faixa média)
        else:
            return 0  # Vazio (faixa alta)

    def log_message(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def connect_arduino(self):
        if self.connection_in_progress:
            return
            
        self.connection_in_progress = True
        self.connection_status.config(text="Conectando...", foreground="orange")
        self.log_message("Conectando ao Arduino...")
        
        def connect():
            try:
                self.log_message(f"Tentando porta: {self.arduino_port}")
                
                if self.ser and self.ser.is_open:
                    self.ser.close()
                
                self.ser = serial.Serial(self.arduino_port, self.baud_rate, timeout=2)
                time.sleep(2)
                
                self.log_message("Porta serial aberta")
                
                start_time = time.time()
                while time.time() - start_time < 5:
                    if self.ser.in_waiting:
                        linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        if linha:
                            self.log_message(f"Arduino: {linha}")
                            if "ARDUINO_PRONTO_3X3_REAL" in linha:
                                self.connected = True
                                self.connection_status.config(text="🟢 Conectado", foreground="green")
                                self.calibrate_btn.config(state=tk.NORMAL)
                                self.read_btn.config(state=tk.NORMAL)
                                self.reset_btn.config(state=tk.NORMAL)
                                self.test_btn.config(state=tk.NORMAL)
                                self.log_message("Arduino conectado com sucesso!")
                                self.connection_in_progress = False
                                return
                    time.sleep(0.1)
                
                self.log_message("Timeout - Arduino não encontrado")
                self.connection_status.config(text="Falha na conexão", foreground="red")
                
            except Exception as e:
                self.log_message(f"Erro de conexão: {e}")
                self.connection_status.config(text="Erro de conexão", foreground="red")
            
            self.connection_in_progress = False

        threading.Thread(target=connect, daemon=True).start()

    def force_connection(self):
        self.log_message("Forçando nova conexão...")
        self.connect_arduino()

    def listar_portas(self):
        self.log_message("Listando portas seriais...")
        try:
            portas = serial.tools.list_ports.comports()
            if not portas:
                self.log_message("Nenhuma porta serial encontrada")
                return
            
            for i, porta in enumerate(portas):
                self.log_message(f"{i+1}. {porta.device} - {porta.description}")
                if "Arduino" in porta.description:
                    self.log_message(f" Use: {porta.device}")
            
        except Exception as e:
            self.log_message(f"Erro ao listar portas: {e}")

    def iniciar_calibracao(self):
        self.calibrate_btn.config(state=tk.DISABLED)
        
        threading.Thread(target=self.executar_calibracao, daemon=True).start()

    def executar_calibracao(self):
        try:
            self.ser.write(b"CALIBRAR\n")
            self.log_message("Comando CALIBRAR enviado")
            
            start_time = time.time()
            while time.time() - start_time < 15:
                if self.ser.in_waiting:
                    linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        self.log_message(f"Arduino: {linha}")
                        if "CALIBRACAO_CONCLUIDA" in linha:
                            # Após calibração, faz uma leitura para processar
                            self.processar_calibracao_automatica()
                            break
                time.sleep(0.1)
                
        except Exception as e:
            self.log_message(f"Erro na calibração: {e}")
        finally:
            self.root.after(100, lambda: self.calibrate_btn.config(state=tk.NORMAL))

    def processar_calibracao_automatica(self):
        try:
            self.ser.write(b"LER\n")
            self.log_message("Obtendo dados para calibração...")
            
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.ser.in_waiting:
                    linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linha and "DADOS:" in linha:
                        dados_str = linha.replace("DADOS:", "")
                        lista_valores = [int(x) for x in dados_str.split(",")]
                        dados_calibracao = np.array(lista_valores).reshape(3, 3)
                        self.processar_calibracao_por_luminosidade(dados_calibracao)
                        break
                time.sleep(0.1)
            
        except Exception as e:
            self.log_message(f"Erro no processamento: {e}")

    def processar_calibracao_por_luminosidade(self, dados_calibracao):
        try:
            # Coleta todos os valores
            todos_valores = dados_calibracao.flatten()
            
            # Identifica automaticamente os 3 clusters de luminosidade
            clusters = self.identificar_clusters_luminosidade(todos_valores)
            
            # Ordena os clusters por valor médio (do mais escuro ao mais claro)
            clusters_ordenados = sorted(clusters, key=lambda x: x['media'])
            
            # ATRIBUIÇÃO CORRIGIDA:
            cluster_preto = clusters_ordenados[0]   # Mais escuro: PRETO
            cluster_branco = clusters_ordenados[1]  # Intermediário: BRANCO  
            cluster_vazio = clusters_ordenados[2]   # Mais claro: VAZIO
            
            # Cria o objeto de calibração
            self.calibration_data = CalibrationData(
                thresholds={},  # Será calculado no post_init
                cluster_stats={
                    'preto': cluster_preto,
                    'branco': cluster_branco,
                    'vazio': cluster_vazio
                }
            )
            
            # Determina o mapeamento das linhas
            self.mapear_linhas_automaticamente(dados_calibracao)
            
            self.log_message("CALIBRAÇÃO CONCLUÍDA - Clusterização Automática")
            self.log_message(f"Preto (faixa baixa): {cluster_preto['media']:.1f} [{cluster_preto['min']:.1f}-{cluster_preto['max']:.1f}]")
            self.log_message(f"Branco (faixa média): {cluster_branco['media']:.1f} [{cluster_branco['min']:.1f}-{cluster_branco['max']:.1f}]")
            self.log_message(f"Vazio (faixa alta): {cluster_vazio['media']:.1f} [{cluster_vazio['min']:.1f}-{cluster_vazio['max']:.1f}]")
            self.log_message(f"Limiar Preto-Branco: {self.calibration_data.thresholds['preto_branco']:.1f}")
            self.log_message(f"Limiar Branco-Vazio: {self.calibration_data.thresholds['branco_vazio']:.1f}")
            
            self.calibration_status.config(text="Sistema calibrado", foreground="green")
            
        except Exception as e:
            self.log_message(f"Erro na calibração por luminosidade: {e}")

    def identificar_clusters_luminosidade(self, valores):
        # Ordena os valores
        valores_ordenados = np.sort(valores)
        
        # Divide em 3 grupos iguais
        n = len(valores_ordenados)
        grupo1 = valores_ordenados[:n//3]
        grupo2 = valores_ordenados[n//3:2*n//3]
        grupo3 = valores_ordenados[2*n//3:]
        
        clusters = []
        for grupo in [grupo1, grupo2, grupo3]:
            if len(grupo) > 0:
                clusters.append({
                    'media': np.mean(grupo),
                    'min': np.min(grupo),
                    'max': np.max(grupo),
                    'valores': grupo
                })
        
        return clusters

    def mapear_linhas_automaticamente(self, dados_calibracao):
        medias_linhas = [np.mean(dados_calibracao[i, :]) for i in range(3)]
        
        # Ordena as linhas por luminosidade média
        linhas_ordenadas = sorted(enumerate(medias_linhas), key=lambda x: x[1])
        
        # MAPEAMENTO CORRETO:
        self.mapa_linhas = {}
        self.mapa_linhas[linhas_ordenadas[0][0]] = 'preto'   # Mais escura: PRETO
        self.mapa_linhas[linhas_ordenadas[1][0]] = 'branco'  # Intermediária: BRANCO
        self.mapa_linhas[linhas_ordenadas[2][0]] = 'vazio'   # Mais clara: VAZIO
        
        self.log_message("Mapeamento automático de linhas:")
        for linha_ordenada, media in linhas_ordenadas:
            tipo = self.mapa_linhas[linha_ordenada]
            self.log_message(f"  Linha física {linha_ordenada}: {tipo} (média: {media:.1f})")

    def solicitar_leitura(self):
        if not self.connected:
            messagebox.showerror("Erro", "Conecte o Arduino primeiro.")
            return
            
        self.log_message("Solicitando leitura...")
        self.read_btn.config(state=tk.DISABLED)
        
        def fazer_leitura():
            try:
                self.ser.write(b"LER\n")
                
                dados_recebidos = False
                start_time = time.time()
                
                while not dados_recebidos and (time.time() - start_time) < 10:
                    if self.ser.in_waiting:
                        linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        if linha:
                            self.log_message(f"Arduino: {linha}")
                            
                            if "DADOS:" in linha:
                                if self.processar_dados_completos(linha):
                                    self.root.after(100, self.update_board_displays)
                                    dados_recebidos = True
                                    break
                            
                            elif "LEITURA_CONCLUIDA" in linha:
                                self.log_message("Leitura concluída")
                
                if not dados_recebidos:
                    self.log_message("TIMEOUT: Dados incompletos recebidos")
                    
            except Exception as e:
                self.log_message(f"ERRO NA LEITURA: {e}")
            finally:
                self.root.after(100, lambda: self.read_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=fazer_leitura, daemon=True).start()

    def processar_dados_completos(self, linha_dados: str):
        try:
            dados_str = linha_dados.replace("DADOS:", "")
            lista_valores = [int(x) for x in dados_str.split(",")]
            self.dados_matriz = np.array(lista_valores).reshape(3, 3)
            
            # Classifica as casas
            if self.calibration_data:
                self.dados_classificados = np.zeros((3, 3), dtype=int)
                for i in range(3):
                    for j in range(3):
                        self.dados_classificados[i, j] = self.classificar_casa(self.dados_matriz[i, j])
                
                # Converte classificação para estado básico (sem identidade das peças)
                estado_basico = self.classificacao_para_estado_basico(self.dados_classificados)
                
                # Aplica a lógica Markoviana para detectar movimento
                novo_estado = self.aplicar_logica_markoviana(estado_basico)
                
                if novo_estado:
                    self.pecas_tabuleiro = novo_estado
                    self.salvar_estado_atual()
                    self.vez_das_brancas = not self.vez_das_brancas
                    self.log_message(f"Movimento detectado - turno alternado para {'BRANCAS' if self.vez_das_brancas else 'PRETAS'}")
                else:
                    self.log_message("Nenhum movimento válido detectado")
            
            self.log_message("Dados processados com sucesso")
            return True
            
        except Exception as e:
            self.log_message(f"Erro ao processar dados completos: {e}")
            return False

    def classificacao_para_estado_basico(self, classificacao: np.ndarray) -> List[List[str]]:
        estado = [['·', '·', '·'], ['·', '·', '·'], ['·', '·', '·']]
        
        for i in range(3):
            for j in range(3):
                classe = classificacao[i, j]
                if classe == 1:  # Branco
                    estado[i][j] = 'B'  # Branco genérico
                elif classe == 2:  # Preto
                    estado[i][j] = 'P'  # Preto genérico
        return estado
    
    def aplicar_logica_markoviana(self, estado_basico: List[List[str]]) -> Optional[List[List[str]]]:
        if self.estado_anterior is None:
            return estado_basico
        
        # Encontra todas as diferenças
        diferencas = []
        for i in range(3):
            for j in range(3):
                anterior = self.estado_anterior[i][j]
                atual = estado_basico[i][j]
                
                # Só considera diferença se houve mudança de categoria (não apenas flutuação dentro da mesma categoria)
                categoria_anterior = self.obter_categoria_peca(anterior)
                categoria_atual = self.obter_categoria_peca(atual)
                
                if categoria_anterior != categoria_atual:
                    diferencas.append((i, j, anterior, atual, categoria_anterior, categoria_atual))
        
        # Log das diferenças detectadas
        if diferencas:
            self.log_message(f"Diferenças detectadas: {len(diferencas)}")
            for diff in diferencas:
                self.log_message(f"  [{diff[0]},{diff[1]}] '{diff[2]}'->'{diff[4]}' -> '{diff[3]}'->'{diff[5]}'")
        
        # Analisa o padrão de diferenças
        movimento = self.analisar_padrao_movimento_corrigido(diferencas, estado_basico)
        
        if movimento:
            return movimento
        else:
            if diferencas:
                self.log_message("Padrão de movimento inválido detectado")
            return None

    def obter_categoria_peca(self, peca: str) -> str:
        if peca == '·':
            return 'vazio'
        elif peca in ['A', 'B', 'C', 'B']:
            return 'branco'
        elif peca in ['a', 'b', 'c', 'P']:
            return 'preto'
        else:
            return 'desconhecido'

    def analisar_padrao_movimento_corrigido(self, diferencas: List[Tuple], estado_basico: List[List[str]]) -> Optional[List[List[str]]]:
        if len(diferencas) == 0:
            return None  # Sem movimento
        
        # Caso (a) Movimento simples
        if len(diferencas) == 2:
            return self.processar_movimento_simples_corrigido(diferencas, estado_basico)
        
        # Caso (b) Captura 
        elif len(diferencas) == 2:
            movimento_captura = self.processar_captura_corrigida(diferencas, estado_basico)
            if movimento_captura:
                return movimento_captura
        
        else:
            self.log_message(f"Padrão não reconhecido: {len(diferencas)} casas alteradas")
            return None

    def processar_movimento_simples_corrigido(self, diferencas: List[Tuple], estado_basico: List[List[str]]) -> Optional[List[List[str]]]:
        # Identifica origem e destino
        origem = None
        destino = None
        
        for i, j, anterior, atual, cat_anterior, cat_atual in diferencas:
            if cat_anterior in ['branco', 'preto'] and cat_atual == 'vazio':
                origem = (i, j, anterior, cat_anterior)  # Casa que tinha peça e ficou vazia
            elif cat_anterior == 'vazio' and cat_atual in ['branco', 'preto']:
                destino = (i, j, atual, cat_atual)  # Casa que estava vazia e tem peça agora
        
        if origem and destino:
            # Verifica se é turno correto
            peca_movida = origem[2]
            cor_peca = 'branca' if origem[3] == 'branco' else 'preta'
            
            if (cor_peca == 'branca' and not self.vez_das_brancas) or (cor_peca == 'preta' and self.vez_das_brancas):
                self.log_message(f"Movimento de peça errada: {peca_movida} no turno das {'brancas' if self.vez_das_brancas else 'pretas'}")
                return None
            
            # Cria novo estado mantendo a identidade da peça
            novo_estado = [linha[:] for linha in self.estado_anterior]
            
            # Move a peça mantendo sua identidade
            peca_identidade = self.estado_anterior[origem[0]][origem[1]]
            novo_estado[origem[0]][origem[1]] = '·'
            novo_estado[destino[0]][destino[1]] = peca_identidade
            
            self.log_message(f"Movimento simples: {peca_identidade} de {chr(65+origem[1])}{3-origem[0]} para {chr(65+destino[1])}{3-destino[0]}")
            return novo_estado
        
        return None

    def processar_captura_corrigida(self, diferencas: List[Tuple], estado_basico: List[List[str]]) -> Optional[List[List[str]]]:
        # Encontra origem e destino
        origem = None
        destino = None
        
        for i, j, anterior, atual, cat_anterior, cat_atual in diferencas:
            if cat_anterior in ['branco', 'preto'] and cat_atual == 'vazio':
                origem = (i, j, anterior, cat_anterior)
            elif cat_anterior in ['branco', 'preto'] and cat_atual in ['branco', 'preto']:
                destino = (i, j, anterior, cat_anterior, atual, cat_atual)
        
        if origem and destino:
            # Verifica se a captura é válida (cores diferentes)
            peca_movida = origem[2]
            peca_capturada = destino[2]  # Peça que estava no destino anteriormente
            
            cor_movida = 'branca' if origem[3] == 'branco' else 'preta'
            cor_capturada = 'branca' if destino[3] == 'branco' else 'preta'
            
            if cor_movida == cor_capturada:
                self.log_message(f"Captura inválida: {peca_movida} não pode capturar {peca_capturada} (mesma cor)")
                return None
            
            # Verifica turno
            if (cor_movida == 'branca' and not self.vez_das_brancas) or (cor_movida == 'preta' and self.vez_das_brancas):
                self.log_message(f"Movimento de peça errada: {peca_movida} no turno das {'brancas' if self.vez_das_brancas else 'pretas'}")
                return None
            
            # Cria novo estado
            novo_estado = [linha[:] for linha in self.estado_anterior]
            
            # Executa a captura
            novo_estado[origem[0]][origem[1]] = '·'
            novo_estado[destino[0]][destino[1]] = peca_movida  # A peça que moveu ocupa o destino
            
            self.log_message(f"Captura: {peca_movida} capturou {peca_capturada} em {chr(65+destino[1])}{3-destino[0]}")
            return novo_estado
        
        return None

    def resetar_sistema(self):
        if not self.connected:
            messagebox.showerror("Erro", "Conecte o Arduino primeiro.")
            return
            
        try:
            self.log_message("Resetando sistema...")
            self.ser.write(b"RESET\n")
            
            self.calibration_data = None
            self.dados_matriz = None
            self.mapa_linhas = None
            self.pecas_tabuleiro = self.get_posicao_inicial_pecas()
            self.vez_das_brancas = True
            self.calibration_status.config(text="Sistema não calibrado", foreground="red")
            
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.ser.in_waiting:
                    linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linha and "RESET_CONCLUIDO" in linha:
                        self.log_message("Sistema resetado")
                        self.update_board_displays()
                        break
                time.sleep(0.1)
                
        except Exception as e:
            self.log_message(f"Erro no reset: {e}")

    def teste_comunicacao(self):
        if not self.connected:
            return
            
        try:
            self.log_message("Testando comunicação...")
            self.ser.write(b"TEST\n")
            
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.ser.in_waiting:
                    linha = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if linha:
                        self.log_message(f"Resposta: {linha}")
                        break
                time.sleep(0.1)
                
        except Exception as e:
            self.log_message(f"Erro no teste: {e}")

    def debug_sistema(self):
        self.log_message("DEBUG DO SISTEMA:")
        self.log_message(f"   Conectado: {self.connected}")
        self.log_message(f"   Calibração: {self.calibration_data is not None}")
        self.log_message(f"   Dados matriz: {self.dados_matriz is not None}")
        self.log_message(f"   Mapa linhas: {self.mapa_linhas}")
        self.log_message(f"   Vez das brancas: {self.vez_das_brancas}")
        self.log_message(f"   Estado atual das peças:")
        for i, linha in enumerate(self.pecas_tabuleiro):
            self.log_message(f"     Linha {i}: {linha}")
        if self.estado_anterior:
            self.log_message(f"   Estado anterior:")
            for i, linha in enumerate(self.estado_anterior):
                self.log_message(f"     Linha {i}: {linha}")

    def limpar_log(self):
        self.log_text.delete(1.0, tk.END)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

if __name__ == "__main__":
    app = Xadrez3x3RealInterface()
    app.run()