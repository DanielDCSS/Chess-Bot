// SISTEMA_REAL_3x3_ROBUSTO_V2.ino
const int PINOS_LINHAS[] = {2, 3, 4};
const int PINOS_COLUNAS[] = {A0, A1, A2};
const int NUM_LINHAS = 3;
const int NUM_COLUNAS = 3;

const int NUM_LEITURAS_MEDIA = 20;
const int DELAY_ESTABILIZACAO = 20;
const int DELAY_ENTRE_LINHAS = 10;

int leituras[NUM_LINHAS][NUM_COLUNAS];
bool sistema_calibrado = false;

void setup() {
  Serial.begin(115200);
  
  // Aguarda serial estabilizar
  while (!Serial) {
    delay(10);
  }
  
  // Configura TODOS os pinos digitais inicialmente como INPUT (alta impedância)
  for (int i = 2; i <= 4; i++) {
    pinMode(i, INPUT);
    digitalWrite(i, LOW);
  }
  
  // Configura pinos analógicos
  for (int i = 0; i < NUM_COLUNAS; i++) {
    pinMode(PINOS_COLUNAS[i], INPUT);
  }
  
  Serial.flush();
  delay(2000);
  
  Serial.println("ARDUINO_PRONTO_3X3_REAL_V2");
  Serial.println("Sistema 3x3 Real - Pronto");
}

void loop() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    if (comando == "LER") {
      realizarLeituraIsolada();
      enviarDadosBrutos();
      Serial.println("LEITURA_CONCLUIDA");
    }
    else if (comando == "CALIBRAR") {
      calibrarSistema();
      Serial.println("CALIBRACAO_CONCLUIDA");
    }
    else if (comando == "RESET") {
      sistema_calibrado = false;
      Serial.println("RESET_CONCLUIDO");
    }
    else if (comando == "TEST") {
      Serial.println("TESTE_OK");
    }
    
    Serial.flush();
  }
  delay(50);
}

void realizarLeituraIsolada() {
  long leiturasAcumuladas[NUM_LINHAS][NUM_COLUNAS] = {0};
  
  for (int leitura = 0; leitura < NUM_LEITURAS_MEDIA; leitura++) {
    for (int linha = 0; linha < NUM_LINHAS; linha++) {
      // PRIMEIRO: Coloca TODAS as linhas em LOW/INPUT para garantir isolamento
      for (int l = 0; l < NUM_LINHAS; l++) {
        if (l != linha) {
          pinMode(PINOS_LINHAS[l], INPUT);
          digitalWrite(PINOS_LINHAS[l], LOW);
        }
      }
      
      // AGORA ativa apenas a linha atual
      pinMode(PINOS_LINHAS[linha], OUTPUT);
      digitalWrite(PINOS_LINHAS[linha], HIGH);
      delay(DELAY_ESTABILIZACAO);
      
      // Leitura das colunas para esta linha
      for (int coluna = 0; coluna < NUM_COLUNAS; coluna++) {
        pinMode(PINOS_COLUNAS[coluna], OUTPUT);
        digitalWrite(PINOS_COLUNAS[coluna], LOW);
        pinMode(PINOS_COLUNAS[coluna], INPUT);
    
        for (int errado = 0; errado < NUM_COLUNAS; errado++){
          if (errado != coluna){
            pinMode(PINOS_COLUNAS[errado], OUTPUT);
            digitalWrite(PINOS_COLUNAS[errado], HIGH);
          }

        }
        int valor = analogRead(PINOS_COLUNAS[coluna]);
        leiturasAcumuladas[linha][coluna] += valor;
      }
      
      // Desativa a linha atual
      digitalWrite(PINOS_LINHAS[linha], LOW);
      pinMode(PINOS_LINHAS[linha], INPUT);
      delay(DELAY_ENTRE_LINHAS);
    }
    delay(5);
  }
  
  // Calcula médias
  for (int linha = 0; linha < NUM_LINHAS; linha++) {
    for (int coluna = 0; coluna < NUM_COLUNAS; coluna++) {
      leituras[linha][coluna] = leiturasAcumuladas[linha][coluna] / NUM_LEITURAS_MEDIA;
    }
  }
}

void calibrarSistema() {
  Serial.println("CALIBRACAO: Iniciando calibração automática...");
  Serial.println("CALIBRACAO: Posicione peças BRANCAS na linha 0");
  Serial.println("CALIBRACAO: Deixe VAZIO na linha 1");
  Serial.println("CALIBRACAO: Posicione peças PRETAS na linha 2");
  Serial.println("CALIBRACAO: Aguardando 5 segundos...");
  
  delay(5000);
  
  realizarLeituraIsolada();
  
  // Calcula estatísticas
  long somaVazio = 0, somaBranco = 0, somaPreto = 0;
  int countVazio = 0, countBranco = 0, countPreto = 0;
  
  for (int linha = 0; linha < NUM_LINHAS; linha++) {
    for (int coluna = 0; coluna < NUM_COLUNAS; coluna++) {
      int valor = leituras[linha][coluna];
      
      if (linha == 1) { // Linha do meio - vazia
        somaVazio += valor;
        countVazio++;
      } else if (linha == 0) { // Linha superior - brancas
        somaBranco += valor;
        countBranco++;
      } else if (linha == 2) { // Linha inferior - pretas
        somaPreto += valor;
        countPreto++;
      }
    }
  }
  
  int mediaVazio = (countVazio > 0) ? somaVazio / countVazio : 500;
  int mediaBranco = (countBranco > 0) ? somaBranco / countBranco : 800;
  int mediaPreto = (countPreto > 0) ? somaPreto / countPreto : 200;
  
  Serial.print("CALIBRACAO: Vazio: "); Serial.println(mediaVazio);
  Serial.print("CALIBRACAO: Branco: "); Serial.println(mediaBranco);
  Serial.print("CALIBRACAO: Preto: "); Serial.println(mediaPreto);
  
  sistema_calibrado = true;
  Serial.println("CALIBRACAO: Sistema calibrado com sucesso!");
}

void enviarDadosBrutos() {
  Serial.print("DADOS:");
  for (int i = 0; i < NUM_LINHAS; i++) {
    for (int j = 0; j < NUM_COLUNAS; j++) {
      Serial.print(leituras[i][j]);
      if (!(i == NUM_LINHAS-1 && j == NUM_COLUNAS-1)) Serial.print(",");
    }
  }
  Serial.println();
}