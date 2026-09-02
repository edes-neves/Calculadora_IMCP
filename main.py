import os
import sys
import webbrowser
from tkinter import Menu, messagebox
from urllib.parse import quote

import customtkinter as ctk
from PIL import Image, ImageTk

import grafico
import relatorio
from database import Database, LIMITES

COR_PRIMARIA = "#14C9A9"
COR_PRIMARIA_HOVER = "#0FAF93"
COR_PERIGO = "#E74C3C"
COR_AVISO = "#F39C12"
COR_SUCESSO = "#27AE60"
COR_INFO = "#3B9DFF"
COR_TEXTO_MUT = "#8A8F98"
EMAIL_SUPORTE = "nevestecnologias@gmail.com"


class AppIMC(ctk.CTk):
    def __init__(self):
        super().__init__(baseName="CalculadoraDeIMCProfissional",
                         className="CalculadoraDeIMCProfissional")

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.db = Database()
        self.perfil_atual_id = None
        self._imagem_barra = None
        self._imagem_grafico = None

        self.title("Calculadora de IMC Profissional")
        self.wm_title("Calculadora de IMC Profissional")
        self.geometry("900x760")
        self.resizable(True, True)

        self._configurar_icone()

    def _configurar_icone(self):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icone = os.path.join(base, "icone.png")
        if os.path.exists(icone):
            self._icone_janela = ImageTk.PhotoImage(Image.open(icone).resize((64, 64), Image.LANCZOS))
            self.iconphoto(True, self._icone_janela)

        self._configurar_header()
        self._configurar_menubar()

        self.abas = ctk.CTkTabview(
            self,
            command=lambda: self._ao_trocar_aba(),
            corner_radius=18,
            fg_color=("#FFFFFF", "#1E2126"),
            segmented_button_fg_color=("#E8EDF0", "#2A2E34"),
            segmented_button_selected_color=COR_PRIMARIA,
            segmented_button_selected_hover_color=COR_PRIMARIA_HOVER,
            segmented_button_unselected_hover_color=("#D8DEE4", "#393E46"),
        )
        self.abas.pack(fill="both", expand=True, padx=18, pady=(6, 16))

        self.tab_perfil = self.abas.add("Perfil")
        self.tab_calculo = self.abas.add("Calcular IMC")
        self.tab_historico = self.abas.add("Histórico")
        self.tab_evolucao = self.abas.add("Evolução")
        self.tab_meta = self.abas.add("Meta de Peso")

        self.configurar_tela_perfil()
        self.configurar_tela_calculo()
        self.configurar_tela_historico()
        self.configurar_tela_evolucao()
        self.configurar_tela_meta()

        self.carregar_perfis()
        if self.perfis:
            self.selecionar_perfil(self.perfis[0][0])

    def _configurar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(header, text="Calculadora de IMC",
                     font=("Arial", 24, "bold")).pack(side="left")
        ctk.CTkLabel(header, text="Profissional",
                     font=("Arial", 24, "bold"), text_color=COR_PRIMARIA).pack(side="left")

        self.btn_tema = ctk.CTkButton(
            header, text="Modo Escuro", width=130, height=34, corner_radius=17,
            fg_color=("#22262B", "#3A3F46"), hover_color=("#33383F", "#4A5058"),
            text_color=("#333333", "#E6E6E6"), command=self._alternar_tema)
        self.btn_tema.pack(side="right")

        ctk.CTkLabel(header, text="  Índice de Massa Corporal",
                     font=("Arial", 13), text_color=COR_TEXTO_MUT).pack(side="right")

    def _alternar_tema(self):
        novo = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(novo)
        self.btn_tema.configure(text="Modo Escuro" if novo == "Dark" else "Modo Claro")
        self.lbl_perfil_msg.configure(text=self.lbl_perfil_msg.cget("text"))
        self._ajustar_cores_menubar()

    # ------------------------------------------------------------------
    # Barra de menus
    # ------------------------------------------------------------------
    def _configurar_menubar(self):
        self._menubar = Menu(self, tearoff=0)
        self._menus = {}

        menu_arquivo = Menu(self._menubar, tearoff=0)
        menu_arquivo.add_command(label="Exportar PDF (resultado)", command=self.exportar_pdf)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.destroy)

        menu_editar = Menu(self._menubar, tearoff=0)
        menu_editar.add_command(label="Novo Perfil", command=lambda: self._ir_para_aba("Perfil"))
        menu_editar.add_command(label="Editar Perfil Atual", command=self.editar_perfil_atual)
        menu_editar.add_command(label="Excluir Perfil Atual", command=self.excluir_perfil_atual)

        menu_exibir = Menu(self._menubar, tearoff=0)
        menu_exibir.add_command(label="Alternar tema (Escuro/Claro)", command=self._alternar_tema)
        menu_exibir.add_separator()
        for nome_aba in ("Perfil", "Calcular IMC", "Histórico", "Evolução", "Meta de Peso"):
            menu_exibir.add_command(
                label=f"Ir para: {nome_aba}",
                command=lambda a=nome_aba: self._ir_para_aba(a))

        menu_historicos = Menu(self._menubar, tearoff=0)
        menu_historicos.add_command(label="Ver Histórico", command=lambda: self._ir_para_aba("Histórico"))
        menu_historicos.add_command(label="Ver Evolução", command=lambda: self._ir_para_aba("Evolução"))
        menu_historicos.add_separator()
        menu_historicos.add_command(label="Limpar histórico deste perfil", command=self.limpar_historico)

        menu_ajuda = Menu(self._menubar, tearoff=0)
        menu_ajuda.add_command(label="Relatar um problema",
                               command=lambda: self._abrir_email("Relatar um problema - Calculadora de IMC"))
        menu_ajuda.add_command(label="Enviar uma sugestão",
                               command=lambda: self._abrir_email("Sugestão - Calculadora de IMC"))
        menu_ajuda.add_command(label="Contato",
                               command=lambda: self._abrir_email("Contato - Calculadora de IMC"))
        menu_ajuda.add_command(label="Sobre", command=self._sobre)

        self._menubar.add_cascade(label="Arquivo", menu=menu_arquivo)
        self._menubar.add_cascade(label="Editar", menu=menu_editar)
        self._menubar.add_cascade(label="Exibir", menu=menu_exibir)
        self._menubar.add_cascade(label="Históricos", menu=menu_historicos)
        self._menubar.add_cascade(label="Ajuda", menu=menu_ajuda)
        self._menus = {"arquivo": menu_arquivo, "editar": menu_editar,
                       "exibir": menu_exibir, "historicos": menu_historicos, "ajuda": menu_ajuda}
        self.config(menu=self._menubar)
        self._ajustar_cores_menubar()

    def _ajustar_cores_menubar(self):
        escuro = ctk.get_appearance_mode() == "Dark"
        bg = ("#1E2126" if escuro else "#F5F7FA")
        fg = ("#E6E6E6" if escuro else "#1F2937")
        ativo_bg = ("#2A2E34" if escuro else "#E0E7EC")
        ativo_fg = ("#FFFFFF" if escuro else "#111827")
        for menu in (self._menubar, *self._menus.values()):
            menu.configure(bg=bg, fg=fg, activebackground=ativo_bg, activeforeground=ativo_fg,
                           bd=0, relief="flat", font=("Arial", 12))

    def _ir_para_aba(self, nome):
        self.abas.set(nome)
        self.atualizar_telas_do_perfil()

    def _abrir_email(self, assunto):
        url = f"mailto:{EMAIL_SUPORTE}?subject={quote(assunto)}"
        webbrowser.open(url)

    def _sobre(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Sobre")
        dialog.geometry("560x500")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.lift()
        dialog.focus_force()

        ctk.CTkLabel(dialog, text="Calculadora de IMC Profissional",
                     font=("Arial", 22, "bold")).pack(pady=(24, 6))
        ctk.CTkLabel(dialog, text="Índice de Massa Corporal",
                     font=("Arial", 14), text_color=COR_TEXTO_MUT).pack()

        ctk.CTkFrame(dialog, height=2, corner_radius=1,
                     fg_color=COR_PRIMARIA).pack(fill="x", padx=40, pady=14)

        descricao = (
            "Este programa calcula o Índice de Massa Corporal (IMC), "
            "classifica o resultado de acordo com as faixas oficiais e identifica a situação "
            "de cada paciente. Ele gerencia perfis individuais, registra o histórico de medições, "
            "acompanha a evolução por meio de gráficos, define metas de peso e gera "
            "relatórios em PDF."
        )
        ctk.CTkLabel(dialog, text=descricao, font=("Arial", 14, "bold"),
                     wraplength=480, justify="center").pack(padx=32, pady=(4, 16))

        ctk.CTkLabel(dialog, text=f"Desenvolvedor: José Edes Neves",
                     font=("Arial", 15, "bold"), text_color=COR_PRIMARIA).pack(pady=4)
        ctk.CTkLabel(dialog, text=f"Contato: {EMAIL_SUPORTE}",
                     font=("Arial", 12), text_color=COR_TEXTO_MUT).pack(pady=2)

        ctk.CTkFrame(dialog, height=2, corner_radius=1,
                     fg_color=COR_PRIMARIA).pack(fill="x", padx=40, pady=14)

        quadro_licenca = ctk.CTkFrame(dialog, corner_radius=14, fg_color=("#FFFFFF", "#22262D"))
        quadro_licenca.pack(fill="x", padx=32, pady=(0, 8))
        ctk.CTkLabel(quadro_licenca, text="Licença MIT", font=("Arial", 16, "bold"),
                     text_color=COR_AVISO).pack(pady=(12, 4))
        texto_licenca = (
            "Softwares distribuídos sob a licença MIT são livres e de código aberto. "
            "Você tem o direito de usar, copiar, modificar, mesclar, publicar, distribuir, "
            "sublicenciar e até vender cópias do software gratuitamente, para qualquer fim, "
            "sem cobrança de royalties, desde que mantenha o aviso de copyright e esta "
            "permissão em todas as cópias ou partes substanciais, e não haja garantia "
            "alguma sobre o programa."
        )
        ctk.CTkLabel(quadro_licenca, text=texto_licenca, font=("Arial", 12),
                     wraplength=470, justify="center").pack(padx=16, pady=(2, 14))

        ctk.CTkButton(dialog, text="Fechar", width=120, height=38, corner_radius=14,
                      fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER,
                      command=dialog.destroy).pack(pady=16)

    # ------------------------------------------------------------------
    # Tela de Perfil
    # ------------------------------------------------------------------
    def configurar_tela_perfil(self):
        frame_lista = ctk.CTkFrame(self.tab_perfil, corner_radius=18, fg_color=("#FFFFFF", "#22262D"))
        frame_lista.pack(side="left", fill="both", expand=True, padx=(16, 8), pady=16)

        ctk.CTkLabel(frame_lista, text="Pacientes / Perfis",
                     font=("Arial", 18, "bold")).pack(pady=(16, 10))

        self.lista_perfis = ctk.CTkScrollableFrame(frame_lista, height=300, corner_radius=14,
                                                   fg_color="transparent")
        self.lista_perfis.pack(fill="both", expand=True, padx=14, pady=6)

        frame_botoes = ctk.CTkFrame(frame_lista, fg_color="transparent")
        frame_botoes.pack(pady=(8, 16))
        self.btn_editar_perfil = ctk.CTkButton(
            frame_botoes, text="Editar", width=96, height=36, corner_radius=12,
            fg_color=("#1F6AA5", "#1F6AA5"), hover_color=COR_PRIMARIA,
            command=self.editar_perfil_atual)
        self.btn_editar_perfil.grid(row=0, column=0, padx=6)
        self.btn_excluir_perfil = ctk.CTkButton(
            frame_botoes, text="Excluir", width=96, height=36, corner_radius=12,
            fg_color="#D64545", hover_color="#B83838",
            command=self.excluir_perfil_atual)
        self.btn_excluir_perfil.grid(row=0, column=1, padx=6)

        frame_form = ctk.CTkFrame(self.tab_perfil, corner_radius=18, fg_color=("#FFFFFF", "#22262D"))
        frame_form.pack(side="right", fill="y", padx=(8, 16), pady=16, anchor="ne")
        self.lbl_form_titulo = ctk.CTkLabel(frame_form, text="Novo Perfil", font=("Arial", 18, "bold"))
        self.lbl_form_titulo.pack(pady=(16, 12))

        ctk.CTkLabel(frame_form, text="Nome:", font=("Arial", 13)).pack(anchor="w", padx=20)
        self.entry_nome = ctk.CTkEntry(frame_form, width=220, height=38, corner_radius=12,
                                       border_color=("#C8CDD2", "#3A424D"),
                                       placeholder_text="Nome do paciente")
        self.entry_nome.pack(padx=20, pady=(6, 8))

        ctk.CTkLabel(frame_form, text="Idade:", font=("Arial", 13)).pack(anchor="w", padx=20)
        self.entry_nome_idade = ctk.CTkEntry(frame_form, width=220, height=38, corner_radius=12,
                                             border_color=("#C8CDD2", "#3A424D"),
                                             placeholder_text="Ex: 45")
        self.entry_nome_idade.pack(padx=20, pady=(6, 8))

        ctk.CTkLabel(frame_form, text="Gênero:", font=("Arial", 13)).pack(anchor="w", padx=20)
        self.combobox_perfil_genero = ctk.CTkComboBox(frame_form, values=["Masculino", "Feminino", "Outro"],
                                                      width=220, height=38, corner_radius=12,
                                                      border_color=("#C8CDD2", "#3A424D"))
        self.combobox_perfil_genero.set("Masculino")
        self.combobox_perfil_genero.pack(padx=20, pady=(6, 8))

        frame_form_botoes = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_form_botoes.pack(pady=(18, 8))
        self.btn_criar_perfil = ctk.CTkButton(
            frame_form_botoes, text="Criar Perfil", width=130, height=38, corner_radius=14,
            fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER,
            command=self.criar_perfil)
        self.btn_criar_perfil.grid(row=0, column=0, padx=6)
        self.btn_cancelar_edicao = ctk.CTkButton(
            frame_form_botoes, text="Cancelar", width=80, height=38, corner_radius=14,
            fg_color="#6B7280", hover_color="#565E67",
            command=self.cancelar_edicao)
        self.btn_cancelar_edicao.grid(row=0, column=1, padx=6)
        self.btn_cancelar_edicao.grid_remove()

        self._btn_criar_cor = self.btn_criar_perfil.cget("fg_color")
        self._perfil_em_edicao = None

        self.lbl_perfil_msg = ctk.CTkLabel(frame_form, text="", font=("Arial", 12),
                                           text_color=COR_INFO, wraplength=240, justify="center")
        self.lbl_perfil_msg.pack(padx=16, pady=(0, 14))

    def carregar_perfis(self):
        self.perfis = self.db.listar_perfis()
        self._map_seletor = {self._texto_perfil(p): p[0] for p in self.perfis}

        for widget in self.lista_perfis.winfo_children():
            widget.destroy()
        for perfil in self.perfis:
            pid, nome, idade, genero = perfil
            btn = ctk.CTkButton(
                self.lista_perfis,
                text=f"{nome}   ({idade} anos, {genero})",
                font=("Arial", 13),
                anchor="w",
                fg_color=("#E9EEF2", "#2B3037"),
                hover_color=("#D7E7F5", "#2E4B6B"),
                corner_radius=12,
                height=42,
                command=lambda p=pid: self.selecionar_perfil(p),
            )
            btn.pack(fill="x", padx=9, pady=4)

        self._atualizar_combobox_calculo()

    def _texto_perfil(self, perfil):
        nome, idade, genero = perfil[1], perfil[2], perfil[3]
        return f"{nome} ({idade} anos, {genero})"

    def _atualizar_combobox_calculo(self):
        self._atualizando_combobox = True
        valores = list(self._map_seletor.keys())
        for cb in (self.combobox_calculo_perfil, self.combobox_meta_perfil,
                   self.combobox_historico_perfil, self.combobox_evolucao_perfil):
            cb.configure(values=valores)
            cb.set("")
        if self.perfil_atual_id:
            p = self.db.buscar_perfil(self.perfil_atual_id)
            if p:
                texto = self._texto_perfil(p)
                for cb in (self.combobox_calculo_perfil, self.combobox_meta_perfil,
                           self.combobox_historico_perfil, self.combobox_evolucao_perfil):
                    cb.set(texto)
        elif valores:
            for cb in (self.combobox_calculo_perfil, self.combobox_meta_perfil,
                       self.combobox_historico_perfil, self.combobox_evolucao_perfil):
                cb.set(valores[0])
        self._atualizando_combobox = False

    def _ao_escolher_perfil_no_calculo(self, selecionado):
        if getattr(self, "_atualizando_combobox", False):
            return
        pid = self._map_seletor.get(selecionado)
        if pid:
            self.selecionar_perfil(pid)

    def _ao_escolher_perfil_no_historico(self, selecionado):
        self._ao_escolher_perfil_no_calculo(selecionado)

    def _ao_escolher_perfil_na_evolucao(self, selecionado):
        self._ao_escolher_perfil_no_calculo(selecionado)

    def selecionar_perfil(self, perfil_id):
        self.perfil_atual_id = perfil_id
        p = self.db.buscar_perfil(perfil_id)
        if p:
            if not getattr(self, "_atualizando_combobox", False):
                self._atualizando_combobox = True
                texto = self._texto_perfil(p)
                for cb in (self.combobox_calculo_perfil, self.combobox_meta_perfil,
                           self.combobox_historico_perfil, self.combobox_evolucao_perfil):
                    cb.set(texto)
                self._atualizando_combobox = False
            self.lbl_perfil_msg.configure(text=f"Perfil ativo: {p[1]}")
        self.atualizar_telas_do_perfil()

    def criar_perfil(self):
        if self._perfil_em_edicao:
            self.salvar_edicao()
            return
        nome = self.entry_nome.get().strip()
        try:
            idade = int(self.entry_nome_idade.get())
        except ValueError:
            self.lbl_perfil_msg.configure(text="Idade inválida.", text_color=COR_PERIGO)
            return
        genero = self.combobox_perfil_genero.get()

        if not nome:
            self.lbl_perfil_msg.configure(text="Informe o nome.", text_color=COR_PERIGO)
            return
        if not Database.validar_idade(idade):
            self.lbl_perfil_msg.configure(
                text=f"Idade deve estar entre {LIMITES['idade_min']} e {LIMITES['idade_max']}.", text_color=COR_PERIGO)
            return
        if genero not in ("Masculino", "Feminino", "Outro"):
            self.lbl_perfil_msg.configure(text="Selecione o gênero.", text_color=COR_PERIGO)
            return

        pid = self.db.criar_perfil(nome, idade, genero)
        self.carregar_perfis()
        self.selecionar_perfil(pid)
        self.entry_nome.delete(0, "end")
        self.entry_nome_idade.delete(0, "end")
        self.lbl_perfil_msg.configure(text=f"Perfil '{nome}' criado.", text_color=COR_SUCESSO)

    def editar_perfil_atual(self):
        if not self.perfil_atual_id:
            self.lbl_perfil_msg.configure(text="Selecione um perfil na lista para editar.", text_color=COR_PERIGO)
            return
        p = self.db.buscar_perfil(self.perfil_atual_id)
        if not p:
            return

        self._perfil_em_edicao = p[0]
        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, p[1])
        self.entry_nome_idade.delete(0, "end")
        self.entry_nome_idade.insert(0, str(p[2]))
        self.combobox_perfil_genero.set(p[3])

        self.lbl_form_titulo.configure(text="Editar Perfil")
        self.btn_criar_perfil.configure(text="Salvar Alterações", fg_color=COR_SUCESSO)
        self.btn_cancelar_edicao.grid()
        self.lbl_perfil_msg.configure(
            text=f"Editando: {p[1]} — altere os campos e clique em Salvar Alterações.", text_color=COR_INFO)

    def salvar_edicao(self):
        perfil_id = self._perfil_em_edicao
        nome = self.entry_nome.get().strip()
        try:
            idade = int(self.entry_nome_idade.get())
        except ValueError:
            self.lbl_perfil_msg.configure(text="Idade inválida.", text_color=COR_PERIGO)
            return
        genero = self.combobox_perfil_genero.get()

        if not nome:
            self.lbl_perfil_msg.configure(text="Informe o nome.", text_color=COR_PERIGO)
            return
        if not Database.validar_idade(idade):
            self.lbl_perfil_msg.configure(
                text=f"Idade deve estar entre {LIMITES['idade_min']} e {LIMITES['idade_max']}.", text_color=COR_PERIGO)
            return
        if genero not in ("Masculino", "Feminino", "Outro"):
            self.lbl_perfil_msg.configure(text="Selecione o gênero.", text_color=COR_PERIGO)
            return

        self.db.editar_perfil(perfil_id, nome, idade, genero)
        self._sair_modo_edicao()
        self.carregar_perfis()
        self.selecionar_perfil(perfil_id)
        self.lbl_perfil_msg.configure(text=f"Perfil '{nome}' atualizado.", text_color=COR_SUCESSO)

    def cancelar_edicao(self):
        self._sair_modo_edicao()
        self.lbl_perfil_msg.configure(text="Edição cancelada.", text_color=COR_TEXTO_MUT)

    def _sair_modo_edicao(self):
        self._perfil_em_edicao = None
        self.entry_nome.delete(0, "end")
        self.entry_nome_idade.delete(0, "end")
        self.combobox_perfil_genero.set("Masculino")
        self.lbl_form_titulo.configure(text="Novo Perfil")
        self.btn_criar_perfil.configure(text="Criar Perfil", fg_color=self._btn_criar_cor)
        self.btn_cancelar_edicao.grid_remove()

    def excluir_perfil_atual(self):
        if not self.perfil_atual_id:
            return
        p = self.db.buscar_perfil(self.perfil_atual_id)
        if not p:
            return
        if not messagebox.askyesno("Excluir perfil",
                                   f"Excluir '{p[1]}' e todo o histórico dele?"):
            return
        if self._perfil_em_edicao:
            self._sair_modo_edicao()
        self.db.excluir_perfil(self.perfil_atual_id)
        self.carregar_perfis()
        if self.perfis:
            self.selecionar_perfil(self.perfis[0][0])
        else:
            self.perfil_atual_id = None
            self.lbl_perfil_msg.configure(text="Nenhum perfil. Crie um novo.")

    def atualizar_telas_do_perfil(self):
        self.atualizar_label_calculo()
        self.atualizar_lista_historico()
        self.atualizar_tela_evolucao()
        self.atualizar_tela_meta()

    # ------------------------------------------------------------------
    # Tela de Cálculo
    # ------------------------------------------------------------------
    def configurar_tela_calculo(self):
        frame_perfil_calculo = ctk.CTkFrame(self.tab_calculo, fg_color="transparent")
        frame_perfil_calculo.pack(pady=(22, 0))
        ctk.CTkLabel(frame_perfil_calculo, text="Perfil:", font=("Arial", 14, "bold")).pack(side="left", padx=(0, 10))
        self.combobox_calculo_perfil = ctk.CTkComboBox(
            frame_perfil_calculo, values=[], width=340, height=38, corner_radius=12,
            border_color=("#C8CDD2", "#3A424D"),
            state="readonly", command=self._ao_escolher_perfil_no_calculo)
        self.combobox_calculo_perfil.pack(side="left")

        self.lbl_calculo_perfil = ctk.CTkLabel(self.tab_calculo, text="Nenhum perfil selecionado",
                                               font=("Arial", 12), text_color=COR_INFO)
        self.lbl_calculo_perfil.pack(pady=(8, 0))

        frame_inputs = ctk.CTkFrame(self.tab_calculo, corner_radius=18, fg_color=("#FFFFFF", "#22262D"))
        frame_inputs.pack(pady=18, padx=(60, 60), fill="x")

        ctk.CTkLabel(frame_inputs, text="Peso (kg):", font=("Arial", 14, "bold")).grid(
            row=0, column=0, padx=(20, 6), pady=(22, 6), sticky="w")
        self.entry_peso = ctk.CTkEntry(frame_inputs,
                                       placeholder_text=f"Ex: 87,8 ou 87.8  (2 - {int(LIMITES['peso_max'])})",
                                       width=180, height=40, corner_radius=12,
                                       border_color=("#C8CDD2", "#3A424D"))
        self.entry_peso.grid(row=1, column=0, padx=(20, 6), pady=(0, 10))

        ctk.CTkLabel(frame_inputs, text="Altura (m):", font=("Arial", 14, "bold")).grid(
            row=0, column=1, padx=6, pady=(22, 6), sticky="w")
        self.entry_altura = ctk.CTkEntry(frame_inputs,
                                         placeholder_text=f"Ex: 1,75, 1.75 ou 175",
                                         width=190, height=40, corner_radius=12,
                                         border_color=("#C8CDD2", "#3A424D"))
        self.entry_altura.grid(row=1, column=1, padx=6, pady=(0, 10))

        self.btn_cm = ctk.CTkButton(frame_inputs, text="Usar cm", width=86, height=38, corner_radius=12,
                                    fg_color=("#94A3B8", "#4A5260"), hover_color=("#7C8AA0", "#5A6373"),
                                    command=self.converter_cm_para_m)
        self.btn_cm.grid(row=1, column=2, rowspan=2, padx=(6, 20), pady=(0, 10))

        self.lbl_limites = ctk.CTkLabel(frame_inputs,
                                        text=f"Limites aceitos: peso {LIMITES['peso_min']}-{LIMITES['peso_max']}kg, "
                                             f"altura {LIMITES['altura_min']}-{LIMITES['altura_max']}m, "
                                             f"idade {LIMITES['idade_min']}-{LIMITES['idade_max']} anos",
                                        font=("Arial", 11), text_color=COR_TEXTO_MUT)
        self.lbl_limites.grid(row=2, column=0, columnspan=3, padx=20, pady=(4, 14))

        self.btn_calcular = ctk.CTkButton(self.tab_calculo, text="Calcular IMC", font=("Arial", 17, "bold"),
                                          height=52, width=300, corner_radius=16,
                                          fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER,
                                          command=self.processar_calculo)
        self.btn_calcular.pack(pady=(14, 8))

        self.frame_resultado = ctk.CTkFrame(self.tab_calculo, corner_radius=18, fg_color=("#FFFFFF", "#22262D"))
        self.frame_resultado.pack(pady=12, padx=(60, 60), fill="both")

        self.lbl_resultado_imc = ctk.CTkLabel(self.frame_resultado, text="---", font=("Arial", 40, "bold"))
        self.lbl_resultado_imc.pack(pady=(18, 2))
        self.lbl_classificacao = ctk.CTkLabel(self.frame_resultado, text="Selecione um perfil e preencha os dados",
                                              font=("Arial", 17, "bold"))
        self.lbl_classificacao.pack(pady=2)
        self.lbl_peso_ideal = ctk.CTkLabel(self.frame_resultado, text="", font=("Arial", 13, "italic"),
                                           text_color=COR_TEXTO_MUT)
        self.lbl_peso_ideal.pack(pady=2)

        self.lbl_barra = ctk.CTkLabel(self.frame_resultado, text="")
        self.lbl_barra.pack(pady=8)

        self.btn_exportar = ctk.CTkButton(self.frame_resultado, text="Exportar PDF", font=("Arial", 13),
                                          width=130, height=36, corner_radius=12,
                                          fg_color=("#94A3B8", "#4A5260"), hover_color=("#7C8AA0", "#5A6373"),
                                          command=self.exportar_pdf)
        self.btn_exportar.pack(pady=(4, 16))

    def atualizar_label_calculo(self):
        if not self.perfil_atual_id:
            self.lbl_calculo_perfil.configure(text="Nenhum perfil selecionado")
            return
        p = self.db.buscar_perfil(self.perfil_atual_id)
        if p:
            self.lbl_calculo_perfil.configure(
                text=f"Calculando para: {p[1]}  ({p[2]} anos, {p[3]})")

    def converter_cm_para_m(self):
        try:
            cm = float(AppIMC._limpar_numero(self.entry_altura.get()))
        except ValueError:
            return
        self.entry_altura.delete(0, "end")
        self.entry_altura.insert(0, f"{cm / 100:.2f}")

    @staticmethod
    def _limpar_numero(texto):
        return texto.strip().replace(",", ".")

    @staticmethod
    def _interpretar_altura(texto):
        valor = float(AppIMC._limpar_numero(texto))
        if valor > LIMITES["altura_max"]:
            return valor / 100.0
        return valor

    def processar_calculo(self):
        if not self.perfil_atual_id:
            self.lbl_classificacao.configure(text="Selecione um perfil primeiro.", text_color=COR_PERIGO)
            return
        p = self.db.buscar_perfil(self.perfil_atual_id)
        if not p:
            return
        idade = p[2]
        genero = p[3]
        self._ultimo_perfil_calculo = p

        try:
            peso = float(AppIMC._limpar_numero(self.entry_peso.get()))
            altura = AppIMC._interpretar_altura(self.entry_altura.get())
        except ValueError:
            self._erro_calculo("Digite valores numéricos válidos para peso e altura.")
            return

        if not Database.validar_peso(peso):
            self._erro_calculo(f"Peso deve estar entre {LIMITES['peso_min']} e {LIMITES['peso_max']} kg.")
            return
        if not Database.validar_altura(altura):
            self._erro_calculo(f"Altura deve estar entre {LIMITES['altura_min']} e {LIMITES['altura_max']} m.")
            return

        imc, classe = self.db.salvar_registro(self.perfil_atual_id, peso, altura, idade, genero)
        p_min, p_max = self.db.calcular_peso_ideal(altura, idade)

        cor_texto = self._cor_para_classificacao(classe)
        self._ultimo_resultado = (peso, altura, imc, classe, p_min, p_max, cor_texto)

        self.lbl_resultado_imc.configure(text=f"IMC: {imc}", text_color=cor_texto)
        self.lbl_classificacao.configure(text=classe, text_color=cor_texto)
        self.lbl_peso_ideal.configure(
            text=f"Para esta altura, a faixa de peso recomendada é de {p_min:.1f}kg a {p_max:.1f}kg.",
            text_color=COR_TEXTO_MUT)

        try:
            barras_png = grafico.gerar_barra_imc(imc, idade)
            self._imagem_barra = ctk.CTkImage(light_image=Image.open(grafico._png_mem(barras_png)),
                                              dark_image=Image.open(grafico._png_mem(barras_png)), size=(560, 90))
            self.lbl_barra.configure(image=self._imagem_barra, text="")
        except Exception:
            pass

        self.atualizar_lista_historico()
        self.atualizar_tela_evolucao()
        self.atualizar_tela_meta()

    def _erro_calculo(self, mensagem):
        self.lbl_resultado_imc.configure(text="Erro", text_color=COR_PERIGO)
        self.lbl_classificacao.configure(text=mensagem, text_color=COR_PERIGO)
        self.lbl_peso_ideal.configure(text="")
        self.lbl_barra.configure(image="", text="")

    @staticmethod
    def _cor_para_classificacao(classe):
        if "Grau III" in classe or classe == "Obesidade":
            return "#FF5A5F"
        if "Grau II" in classe:
            return "#F97316"
        if "Grau I" in classe:
            return "#FF9F1C"
        if "Sobrepeso" in classe:
            return "#F5B041"
        if "Normal" in classe:
            return "#2ECC71"
        if "Baixo Peso" in classe or "Abaixo do Peso" in classe:
            return "#00B4D8"
        return "#333333" if ctk.get_appearance_mode() == "Light" else "#FFFFFF"

    def exportar_pdf(self):
        if not getattr(self, "_ultimo_resultado", None):
            messagebox.showinfo("Exportar PDF", "Calcule um IMC primeiro para exportar.")
            return
        p = getattr(self, "_ultimo_perfil_calculo", None)
        peso, altura, imc, classe, p_min, p_max, cor = self._ultimo_resultado

        nome_sugerido = f"relatorio_imc_{p[1].replace(' ', '_')}.pdf"
        caminho = self._selecionar_local_para_salvar(nome_sugerido)
        if not caminho:
            return

        perfil = self.db.buscar_perfil(self.perfil_atual_id)
        meta = perfil[4] if perfil else None
        try:
            relatorio.gerar_pdf_relatorio(
                caminho, p[1], p[2], p[3], peso, altura, imc, classe, p_min, p_max, cor, meta)
            messagebox.showinfo("Exportar PDF", f"Relatório salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o PDF:\n{e}")

    def _selecionar_local_para_salvar(self, nome_sugerido):
        """Abre a navegação a partir da pasta do usuário, sem exibir pastas ocultas ('.*')."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Salvar PDF")
        dialog.geometry("620x520")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.lift()
        dialog.focus_force()

        pasta = {"atual": os.path.expanduser("~")}
        resultado = {"caminho": None}

        frame_nav = ctk.CTkFrame(dialog, corner_radius=14)
        frame_nav.pack(fill="x", padx=14, pady=(14, 6))
        ctk.CTkLabel(frame_nav, text="Pasta:", font=("Arial", 13)).pack(side="left", padx=(8, 6))
        entry_pasta = ctk.CTkEntry(frame_nav, width=300, height=36, corner_radius=10)
        entry_pasta.pack(side="left", padx=(0, 6))
        btn_ir = ctk.CTkButton(frame_nav, text="Ir", width=46, height=36, corner_radius=12)
        btn_ir.pack(side="left", padx=(0, 6))
        btn_home = ctk.CTkButton(frame_nav, text="Início", width=70, height=36, corner_radius=12,
                                 fg_color=COR_INFO)
        btn_home.pack(side="left")

        lista = ctk.CTkScrollableFrame(dialog, width=590, height=280, corner_radius=14)
        lista.pack(fill="both", expand=True, padx=14, pady=6)

        frame_nome = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_nome.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(frame_nome, text="Nome do arquivo:", font=("Arial", 13)).pack(side="left", padx=(0, 8))
        entry_nome = ctk.CTkEntry(frame_nome, width=360, height=36, corner_radius=10)
        entry_nome.insert(0, nome_sugerido)
        entry_nome.pack(side="left")

        frame_acoes = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_acoes.pack(pady=10)
        btn_cancelar = ctk.CTkButton(frame_acoes, text="Cancelar", width=110, height=38, corner_radius=13,
                                     fg_color="#6B7280", hover_color="#565E67", command=dialog.destroy)
        btn_cancelar.pack(side="left", padx=8)
        btn_salvar = ctk.CTkButton(frame_acoes, text="Salvar aqui", width=130, height=38, corner_radius=13,
                                   fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER)
        btn_salvar.pack(side="left", padx=8)

        def navegar(path):
            pasta["atual"] = path
            listar()

        def ir_para_digitada():
            path = entry_pasta.get().strip() or os.path.expanduser("~")
            path = os.path.expanduser(path)
            if os.path.isdir(path):
                navegar(path)

        def salvar_aqui():
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showerror("Erro", "Informe o nome do arquivo.")
                return
            if not nome.lower().endswith(".pdf"):
                nome += ".pdf"
            resultado["caminho"] = os.path.join(pasta["atual"], nome)
            dialog.destroy()

        def listar():
            for w in lista.winfo_children():
                w.destroy()
            try:
                itens = sorted(os.listdir(pasta["atual"]))
            except OSError:
                itens = []

            pai = os.path.dirname(pasta["atual"])
            if pai != pasta["atual"]:
                nome_pai = os.path.basename(pai) or "/"
                b = ctk.CTkButton(lista, text=f"..  Voltar ({nome_pai})", anchor="w", height=36,
                                  corner_radius=10,
                                  fg_color=("#E3E8EC", "#32373F"), hover_color=("#D2D9DF", "#3C424B"),
                                  text_color=("#333333", "#E6E6E6"), command=lambda: navegar(pai))
                b.pack(fill="x", pady=2)

            for nome in itens:
                caminho = os.path.join(pasta["atual"], nome)
                if os.path.isdir(caminho) and not nome.startswith("."):
                    b = ctk.CTkButton(lista, text=nome, anchor="w", height=36, corner_radius=10,
                                      fg_color="transparent", hover_color=("#3A4654", "#2E4B6B"),
                                      text_color=("#3A4654", "#E6E6E6"),
                                      command=lambda c=caminho: navegar(c))
                    b.pack(fill="x", pady=2)

            entry_pasta.delete(0, "end")
            entry_pasta.insert(0, pasta["atual"])

        btn_ir.configure(command=ir_para_digitada)
        btn_home.configure(command=lambda: navegar(os.path.expanduser("~")))
        entry_pasta.bind("<Return>", lambda e: ir_para_digitada())
        btn_salvar.configure(command=salvar_aqui)

        listar()
        self.wait_window(dialog)
        return resultado["caminho"]

    # ------------------------------------------------------------------
    # Tela de Histórico
    # ------------------------------------------------------------------
    def configurar_tela_historico(self):
        frame_filtro = ctk.CTkFrame(self.tab_historico, fg_color="transparent")
        frame_filtro.pack(pady=(20, 0))
        ctk.CTkLabel(frame_filtro, text="Perfil:", font=("Arial", 13)).pack(side="left", padx=(0, 8))
        self.combobox_historico_perfil = ctk.CTkComboBox(
            frame_filtro, values=[], width=300, height=38, corner_radius=12,
            border_color=("#C8CDD2", "#3A424D"),
            state="readonly", command=self._ao_escolher_perfil_no_historico)
        self.combobox_historico_perfil.pack(side="left")

        self.scroll_historico = ctk.CTkScrollableFrame(self.tab_historico, label_text="Medições do perfil ativo",
                                                       corner_radius=16, fg_color=("#FFFFFF", "#22262D"),
                                                       label_font=("Arial", 13, "bold"))
        self.scroll_historico.pack(fill="both", expand=True, padx=16, pady=14)
        self.btn_limpar_historico = ctk.CTkButton(self.tab_historico, text="Limpar histórico deste perfil",
                                                  width=230, height=38, corner_radius=13,
                                                  fg_color="#D64545", hover_color="#B83838",
                                                  command=self.limpar_historico)
        self.btn_limpar_historico.pack(pady=(0, 14))

    def atualizar_lista_historico(self):
        for widget in self.scroll_historico.winfo_children():
            widget.destroy()

        if not self.perfil_atual_id:
            ctk.CTkLabel(self.scroll_historico, text="Selecione um perfil.", font=("Arial", 13)).pack(pady=20)
            return

        registros = self.db.buscar_historico(self.perfil_atual_id)
        if not registros:
            ctk.CTkLabel(self.scroll_historico,
                         text="Nenhum registro encontrado para este perfil ainda.", font=("Arial", 13)).pack(pady=20)
            return

        for reg in registros:
            peso, altura, imc, classe, data = reg
            cor = self._cor_para_classificacao(classe)
            texto = f"{data}  |  {peso:.1f}kg / {altura:.2f}m  |  IMC: {imc} ({classe})"
            card = ctk.CTkLabel(
                self.scroll_historico, text=texto, font=("Arial", 13), anchor="w", justify="left",
                fg_color=("#EDF1F4", "#2B3037"), height=42, corner_radius=12)
            card.pack(fill="x", pady=5, padx=10)

    def limpar_historico(self):
        if not self.perfil_atual_id:
            return
        if messagebox.askyesno("Limpar histórico", "Apagar todas as medições deste perfil?"):
            self.db.excluir_historico_do_perfil(self.perfil_atual_id)
            self.atualizar_lista_historico()
            self.atualizar_tela_evolucao()
            self.atualizar_tela_meta()

    # ------------------------------------------------------------------
    # Tela de Evolução
    # ------------------------------------------------------------------
    def configurar_tela_evolucao(self):
        frame_filtro = ctk.CTkFrame(self.tab_evolucao, fg_color="transparent")
        frame_filtro.pack(pady=(20, 0))
        ctk.CTkLabel(frame_filtro, text="Perfil:", font=("Arial", 13)).pack(side="left", padx=(0, 8))
        self.combobox_evolucao_perfil = ctk.CTkComboBox(
            frame_filtro, values=[], width=300, height=38, corner_radius=12,
            border_color=("#C8CDD2", "#3A424D"),
            state="readonly", command=self._ao_escolher_perfil_na_evolucao)
        self.combobox_evolucao_perfil.pack(side="left")

        self.lbl_evolucao_titulo = ctk.CTkLabel(self.tab_evolucao, text="Evolução do IMC",
                                                font=("Arial", 18, "bold"))
        self.lbl_evolucao_titulo.pack(pady=14)
        self.lbl_evolucao_img = ctk.CTkLabel(self.tab_evolucao, text="")
        self.lbl_evolucao_img.pack(padx=10, pady=4)

        self.btn_exportar_grafico = ctk.CTkButton(self.tab_evolucao, text="Exportar gráfico (PDF)",
                                                  font=("Arial", 13), width=220, height=38, corner_radius=13,
                                                  fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER,
                                                  command=self.exportar_grafico)
        self.btn_exportar_grafico.pack(pady=(0, 14))

    def exportar_grafico(self):
        png = getattr(self, "_imagem_grafico_png", None)
        p = self.db.buscar_perfil(self.perfil_atual_id) if self.perfil_atual_id else None
        if not png:
            messagebox.showinfo("Exportar gráfico",
                                "Gere a evolução de um perfil (2+ medições) primeiro.")
            return
        nome_sugerido = f"grafico_evolucao_{p[1].replace(' ', '_')}.pdf"
        caminho = self._selecionar_local_para_salvar(nome_sugerido)
        if not caminho:
            return
        try:
            relatorio.gerar_pdf_grafico(caminho, p[1], png)
            messagebox.showinfo("Exportar gráfico", f"Gráfico salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o PDF.\n{e}")

    def atualizar_tela_evolucao(self):
        self.lbl_evolucao_img.configure(image="", text="")
        self._imagem_grafico_png = None
        if not self.perfil_atual_id:
            self.lbl_evolucao_titulo.configure(text="Evolução do IMC — selecione um perfil")
            return
        registros = self.db.buscar_historico_cronologico(self.perfil_atual_id)
        if len(registros) < 2:
            self.lbl_evolucao_titulo.configure(text="Evolução do IMC — são necessárias 2+ medições")
            return
        p = self.db.buscar_perfil(self.perfil_atual_id)
        self.lbl_evolucao_titulo.configure(text=f"Evolução do IMC — {p[1]}")
        datas = [r[4] for r in registros]
        imcs = [r[2] for r in registros]
        try:
            png = grafico.gerar_grafico_evolucao(datas, imcs)
            self._imagem_grafico_png = png
            self._imagem_grafico = ctk.CTkImage(light_image=Image.open(grafico._png_mem(png)),
                                                dark_image=Image.open(grafico._png_mem(png)), size=(620, 320))
            self.lbl_evolucao_img.configure(image=self._imagem_grafico, text="")
        except Exception:
            self.lbl_evolucao_titulo.configure(text="Não foi possível gerar o gráfico.")

    # ------------------------------------------------------------------
    # Tela de Meta de Peso
    # ------------------------------------------------------------------
    def configurar_tela_meta(self):
        frame_meta = ctk.CTkFrame(self.tab_meta, corner_radius=18, fg_color=("#FFFFFF", "#22262D"))
        frame_meta.pack(pady=24, padx=(180, 180), fill="both", expand=True)

        self.lbl_meta_titulo = ctk.CTkLabel(frame_meta, text="Meta de Peso", font=("Arial", 20, "bold"))
        self.lbl_meta_titulo.pack(pady=(26, 14))

        frame_meta_perfil = ctk.CTkFrame(frame_meta, fg_color="transparent")
        frame_meta_perfil.pack(pady=6)
        ctk.CTkLabel(frame_meta_perfil, text="Perfil:", font=("Arial", 13)).pack(side="left", padx=(0, 8))
        self.combobox_meta_perfil = ctk.CTkComboBox(
            frame_meta_perfil, values=[], width=300, height=38, corner_radius=12,
            border_color=("#C8CDD2", "#3A424D"),
            state="readonly", command=self._ao_escolher_perfil_na_meta)
        self.combobox_meta_perfil.pack(side="left")

        self.lbl_meta_perfil = ctk.CTkLabel(frame_meta, text="", font=("Arial", 13))
        self.lbl_meta_perfil.pack(pady=6)

        ctk.CTkLabel(frame_meta, text="Peso meta (kg):", font=("Arial", 13)).pack(pady=10)
        self.entry_meta = ctk.CTkEntry(frame_meta, width=180, height=40, corner_radius=12,
                                       border_color=("#C8CDD2", "#3A424D"),
                                       placeholder_text="Ex: 72")
        self.entry_meta.pack(pady=6)

        self.btn_meta = ctk.CTkButton(frame_meta, text="Definir Meta", width=180, height=40, corner_radius=14,
                                      font=("Arial", 14, "bold"),
                                      fg_color=COR_PRIMARIA, hover_color=COR_PRIMARIA_HOVER,
                                      command=self.definir_meta)
        self.btn_meta.pack(pady=14)

        self.lbl_meta_status = ctk.CTkLabel(frame_meta, text="", font=("Arial", 13, "italic"))
        self.lbl_meta_status.pack(pady=8)

    def _ao_escolher_perfil_na_meta(self, selecionado):
        self._ao_escolher_perfil_no_calculo(selecionado)

    def atualizar_tela_meta(self):
        self.lbl_meta_perfil.configure(text="")
        self.lbl_meta_status.configure(text="")

        if getattr(self, "_atualizando_combobox", False):
            return

        p = self.db.buscar_perfil(self.perfil_atual_id) if self.perfil_atual_id else None
        if not p:
            self.entry_meta.delete(0, "end")
            self.combobox_meta_perfil.set("")
            self.lbl_meta_perfil.configure(text="Selecione um perfil.")
            return
        self.combobox_meta_perfil.set(self._texto_perfil(p))
        self.lbl_meta_perfil.configure(text=f"Perfil: {p[1]}")

        meta = p[4]
        self.entry_meta.delete(0, "end")
        if meta is not None:
            self.entry_meta.insert(0, f"{meta:.1f}")
            self.atualizar_status_meta(meta)

    def definir_meta(self):
        if not self.perfil_atual_id:
            return
        try:
            meta = float(AppIMC._limpar_numero(self.entry_meta.get()))
        except ValueError:
            self.lbl_meta_status.configure(text="Digite um peso válido.", text_color=COR_PERIGO)
            return
        if not Database.validar_peso(meta):
            self.lbl_meta_status.configure(text=f"Meta fora dos limites ({LIMITES['peso_min']}-{LIMITES['peso_max']} kg).",
                                           text_color=COR_PERIGO)
            return
        self.db.definir_meta(self.perfil_atual_id, meta)
        self.atualizar_status_meta(meta)

    def atualizar_status_meta(self, meta):
        registros = self.db.buscar_historico_cronologico(self.perfil_atual_id)
        if not registros:
            self.lbl_meta_status.configure(text=f"Meta definida: {meta:.1f} kg", text_color=COR_SUCESSO)
            return
        atual = registros[-1][0]
        if atual <= meta:
            self.lbl_meta_status.configure(
                text=f"Meta: {meta:.1f} kg — você já está no (ou abaixo do) peso meta! "
                     f"Peso atual: {atual:.1f} kg", text_color=COR_SUCESSO)
        else:
            falta = atual - meta
            self.lbl_meta_status.configure(
                text=f"Meta: {meta:.1f} kg  |  Peso atual: {atual:.1f} kg  |  "
                     f"Faltam ~{falta:.1f} kg para a meta.", text_color=COR_INFO)

    # ------------------------------------------------------------------
    def _ao_trocar_aba(self):
        self.atualizar_telas_do_perfil()


if __name__ == "__main__":
    app = AppIMC()
    app.mainloop()
