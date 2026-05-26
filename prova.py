import gspread
import streamlit as st
import google.generativeai as gen
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
gc = gspread.authorize(creds)
drive_service = build('drive', 'v3', credentials=creds)

fogli_di_valutazione = gc.open("modello per phyton (1)")
workbook_sviluppo = gc.open("workbook")

api_gemini = "AIzaSyCh8uKiLgeoeRI6ik7herjj64LOUiqx2Z0"
gen.configure(api_key=api_gemini)

st.header("Modello di Valutazione Rapida")
files_valutazione = st.file_uploader("Carica i PDF di contesto (multipli)", type=["pdf"], accept_multiple_files=True)


def stimaAI(foglio_valutazione, foglio_logica, lista_file):

    formule_valutazione = {}
    for worksheet in foglio_valutazione.worksheets():
        formule_valutazione[worksheet.title] = worksheet.get_values(value_render_option='FORMULA')

    formule_logica = {}
    for worksheet in foglio_logica.worksheets():
        formule_logica[worksheet.title] = worksheet.get_values(value_render_option='FORMULA')

    modello = gen.GenerativeModel(
        model_name="gemini-3.5-flash",
        system_instruction=(
            "Sei un esperto valutatore immobiliare, nello specifico per la gestione immobiliare di studentati, social housing, residence e simili(nello specifico stai valutando per HOMA SPA). Focalizzati quindi sulla gestione, e gioca con i costi di gestione di input, l'biettivo è avere un setup di gestione profittevole sulla metrica deel foglio dcf\n\n"
            f"IMPORTANTE: i dati di input che puoi cambiare sono formattati con sfondo celeste(blu chiaro). Le valutazioni sono sulla base del dcf con occupancy. Sulla base della seguente contesto se presente : file di valutazione caricati. Prendi i dati disponibili dai documenti e compilali nel foglio(le caselle blu chiaro sono gli input) dopodichè, segui il workbook(foglio logica). Il risultato finale deve essere una serie di canoni(non di affitto delle camere, ma bensì canoni da corrispondere alla società che ha in pancia l'immobile durante la gestione, la voce passiva canone nel dcf del modello)proponibili in base alle combinazioni degli input(ci deve essere anche una valutazione con costo di acquisto e una senza(gestione pura)). Le premesse devono sempre essere realistiche, per stime degli input, se non disponibili dai documenti presentati(come ad esempio il costo di acquisto spesso, oppure sempre il canone d'affitto a mercato libero(prendilo da immobiliare o idealista), tira fuori un dato medio dal web(che sia attendebile, per esempio borsino immobiliare o OMI). Nuovamente, l'output deve essere un canone proponibile(o più di uno, il numero minimo possibile in base ai contesti realizzabili e realistici possibili), con una relazione per punti che giustifica le scelte di ogni input(i. e perchè hai scelto tali canoni per le camere?). La sezione finale della relazione deve essere riguardanete alle premesse di fattibilità e i canoni proponibili. Gioca con diversi valori di distribuzione di camere(oppure di altre variabili non vincolate, come mesi di tursistico, frequenza pulizie etc) per trovare l'ottimo realizzabile, fai sempre conto di queste simulazioni che fai e del perchè. "
             "l'esito finale deve sempre stare all'inizio"
        ),
        generation_config={"temperature": 0.0}
    )

    contenuti_per_gemini = [
        f"--- STRUTTURA DEL FOGLIO DI VALUTAZIONE ---\n{formule_valutazione}\n\n"
        f"--- WORKBOOK CON LOGICA PER LO SVILUPPO ---\n{formule_logica}"
    ]
    cartella_repository = "repository valutazioni passate"

    if os.path.exists(cartella_repository):
        contenuti_per_gemini.append(
            "=== INIZIO REPOSITORY FILE PASSATI (DA USARE SOLO COME RIFERIMENTO DI STRUTTURA/APPROCCIO) ===")
        for file_nome in os.listdir(cartella_repository):
            if file_nome.endswith(".pdf"):
                percorso_completo = os.path.join(cartella_repository, file_nome)
                with open(percorso_completo, "rb") as f:
                    pdf_esempi_bytes = f.read()

                contenuti_per_gemini.append(f"--- FILE DI REPOSITORIO: {file_nome} ---")
                contenuti_per_gemini.append({
                    "mime_type": "application/pdf",
                    "data": pdf_esempi_bytes
                })
        contenuti_per_gemini.append("=== FINE REPOSITORY FILE PASSATI ===")

    for file in lista_file:
        pdf_bytes = file.getvalue()
        contenuti_per_gemini.append({
            "mime_type": "application/pdf",
            "data": pdf_bytes
        })

    risposta = modello.generate_content(contenuti_per_gemini)
    return risposta.text

if st.button("Analizza"):
    if files_valutazione:
        with st.spinner("L'AI sta analizzando i PDF e la logica di sviluppo dei Fogli Google..."):
            risultato = stimaAI(fogli_di_valutazione, workbook_sviluppo, files_valutazione)
            st.markdown(f"**{risultato}**")
    else:
        st.warning("carica almeno un file PDF prima di cliccare su Analizza.")
