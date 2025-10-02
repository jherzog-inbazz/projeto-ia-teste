from PIL import Image
import streamlit as st
import pandas as pd

import re
import ast

from painel.filtro.filtro_relatorio_macro import *
from painel.funcao.funcao_relatorio_macro import *

def app_relatorio_macro():
    
    st.markdown("# Insights de Performance dos Conteúdos" )
    
    base_filtrada = app_filtro_relatorio_macro()

    app_funcao_conceito_basico(base_filtrada)
    
    with st.container():

        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            app_funcao_tipo_post(base_filtrada)

        with col2:
            app_funcao_objetos(base_filtrada)

        with col3:
            app_funcao_serie_dia_tipo(base_filtrada)

    with st.container():

        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.markdown("### Análise de CTA")
            app_funcao_mostrar_cta(base_filtrada)

        with col2:
            st.markdown("### Análise de Tópicos")
            app_funcao_vis_tendencias_topicos(base_filtrada)
        
        with col3:
            st.markdown("### Nuvem de Palavras")
            app_funcao_nuvem_palavras(base_filtrada)

        app_funcao_mostrar_video(base_filtrada)