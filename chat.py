import re
import sys
import os

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QThread,
    QTimer,
    Signal,
    QRect
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSizeGrip,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

#from rag import preguntar

def preguntar(q): import time; time.sleep(2); return f"Respuesta de prueba a **{q}**"

# ============================================================
# CONFIG
# ============================================================

SNAP_MARGIN = 12      # distancia final a los bordes de la pantalla
SNAP_THRESHOLD = 48   # "sensibilidad" del imán
TITLE_H = 48          # alto de la barra de título
PILL_W = 230          # ancho de la píldora minimizada
PILL_H = 54           # alto de la píldora minimizada
WIN_MIN_W, WIN_MIN_H = 340, 280
MAX_INPUT_H = 140
SHADOW_ACTIVA = False  # ponlo en False si el scroll va a tirones

DORADO_CLARO = "#e6cc96"

# Pad alrededor del container: hueco para la sombra
PAD = 16 if SHADOW_ACTIVA else 0

# Imágenes del markdown: se descartan (no hay red ni cacheo)
IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")

SALUDO = (
    "Sistemas en línea, **Operador**. "
    "Soy *Ordis*, tu cephalon de a bordo.\n\n"
    "Pregúntame lo que quieras sobre Warframe."
)


# ============================================================
# HOJA DE ESTILOS
# ============================================================

QSS = """
QWidget {
    color: #e9e5da;
    font-family: "Segoe UI";
    font-size: 10pt;
}

#container {
    background-color: #171512;
    border: 1px solid #3c362a;
    border-radius: 22px;
}

#pill_container {
    background-color: #171512;
    border: 1px solid #4a4030;
    border-radius: 27px;
}

#titlebar {
    background-color: #201c15;
    border-top-left-radius: 21px;
    border-top-right-radius: 21px;
}

#pill_titlebar {
    background-color: #201c15;
    border-radius: 26px;
}

#title {
    color: #e8dcc0;
    font-size: 13px;
    font-weight: 600;
}

#ordis_dot {
    background-color: #c8a865;
    border-radius: 5px;
}

#status_dot {
    background-color: #e5484d;
    border-radius: 5px;
}

#chat_area, #chat_area > QWidget > QWidget {
    background: transparent;
    border: none;
}

#bubble_ai {
    background-color: #242019;
    border: 1px solid #362f24;
    border-radius: 14px;
}

#bubble_user {
    background-color: #3a3122;
    border: 1px solid #5c4e2f;
    border-radius: 14px;
}

#bubble_error {
    background-color: #2c1a17;
    border: 1px solid #7a2e2a;
    border-radius: 14px;
}

#bubble_text {
    background: transparent;
    border: none;
}

#typing_label {
    color: #b3a98f;
    font-style: italic;
}

#input {
    background-color: #211e17;
    border: 1px solid #3c362a;
    border-radius: 12px;
    color: #ece7db;
}

#input:focus {
    border: 1px solid #c8a865;
}

#send {
    background-color: #c8a865;
    color: #241b06;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: bold;
}

#send:hover:enabled {
    background-color: #ddc084;
}

#send:pressed:enabled {
    background-color: #b3945a;
}

#send:disabled {
    background-color: #322c22;
    color: #6a6252;
}

#min_btn, #close_btn {
    background: transparent;
    border: none;
    border-radius: 10px;
    color: #b7ac93;
    font-size: 15px;
}

#min_btn:hover {
    background-color: #332d22;
    color: #e8dcc0;
}

#close_btn:hover {
    background-color: #8b2c2c;
    color: #ffffff;
}

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #3a3428;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #57503c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


# ============================================================
# WORKER
# ============================================================

class Worker(QThread):

    respuesta_lista = Signal(str)
    error = Signal(str)

    def __init__(self, pregunta):
        super().__init__()
        self.pregunta = pregunta

    def run(self):
        try:
            respuesta = preguntar(self.pregunta)
            self.respuesta_lista.emit(respuesta)
        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")


# ============================================================
# BURBUJA DE TEXTO (markdown auto-ajustada)
# ============================================================

class BubbleBrowser(QTextBrowser):
    """QTextBrowser que se dimensiona solo al tamaño de su contenido."""

    def __init__(self):
        super().__init__()
        self.setObjectName("bubble_text")
        self.setFrameShape(QFrame.NoFrame)
        self.setFocusPolicy(Qt.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setOpenExternalLinks(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.document().setDocumentMargin(0)
        self._max_ancho = 430

        self.document().documentLayout().documentSizeChanged.connect(
            self._ajustar_alto
        )

    def set_markdown(self, texto):
        self.setMarkdown(IMG_RE.sub("", texto))
        self._recolor()
        self._recalcular()

    def set_max_width(self, max_ancho):
        self._max_ancho = max_ancho
        self._recalcular()

    # --------------------------------------------------------

    def _recalcular(self):
        doc = self.document()
        doc.setTextWidth(-1)                      # ancho natural (sin cortar)
        natural = doc.size().width()
        w = int(min(max(natural, 40), self._max_ancho))

        if w != self.width():
            self.setFixedWidth(w)                 # dispara re-layout + alto
        else:
            doc.setTextWidth(w)

        self._ajustar_alto(doc.size())

    def _ajustar_alto(self, doc_size):
        self.setFixedHeight(int(doc_size.height()) + 4)

    def _recolor(self):
        """Títulos y enlaces en dorado Orokin."""
        dorado = QColor(DORADO_CLARO)
        doc = self.document()
        block = doc.firstBlock()
        while block.isValid():
            es_titulo = block.blockFormat().headingLevel() > 0
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    cf = frag.charFormat()
                    if es_titulo or cf.isAnchor():
                        nuevo = QTextCharFormat(cf)
                        nuevo.setForeground(dorado)
                        cur = QTextCursor(doc)
                        cur.setPosition(frag.position())
                        cur.setPosition(
                            frag.position() + frag.length(),
                            QTextCursor.KeepAnchor,
                        )
                        cur.setCharFormat(nuevo)
                it += 1
            block = block.next()


# ============================================================
# INPUT MULTILÍNEA (Enter envía, Shift+Enter salta línea)
# ============================================================

class ChatInput(QTextEdit):

    enviar = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("input")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)
        self.document().setDocumentMargin(9)
        self.setFixedHeight(42)
        self.textChanged.connect(self._ajustar_alto)

    def _ajustar_alto(self):
        h = int(self.document().size().height()) + 6
        self.setFixedHeight(max(42, min(h, MAX_INPUT_H)))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
            event.modifiers() & Qt.ShiftModifier
        ):
            self.enviar.emit()
            return
        super().keyPressEvent(event)


# ============================================================
# CHAT WINDOW
# ============================================================

class ChatWindow(QWidget):

    def __init__(self):
        super().__init__()

        # ----------------------------------------------------
        # VENTANA
        # ----------------------------------------------------

        self.setWindowTitle("Ordis AI")
        self.resize(560, 720)
        self.setMinimumSize(WIN_MIN_W, WIN_MIN_H)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        self.minimized = False
        self._animando = False
        self._geometria_previa = None
        self._primera_vez = True
        self._puntos = 0
        self._anim = None
        self.worker = None
        self._bubbles = []
        self._typing_row = None
        self._typing_label = None
        self._typing_timer = None
        self.drag_position = QPoint()

        self.setStyleSheet(QSS)

        # ----------------------------------------------------
        # CONTAINER
        # ----------------------------------------------------

        self.container = QWidget()
        self.container.setObjectName("container")

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ----------------------------------------------------
        # TITLE BAR
        # ----------------------------------------------------

        self.titlebar = QWidget()
        self.titlebar.setObjectName("titlebar")
        self.titlebar.setFixedHeight(TITLE_H)

        title_layout = QHBoxLayout(self.titlebar)
        title_layout.setContentsMargins(14, 0, 8, 0)
        title_layout.setSpacing(8)

        self.ordis_dot = QLabel()
        self.ordis_dot.setObjectName("ordis_dot")
        self.ordis_dot.setFixedSize(10, 10)

        self.title_label = QLabel("Ordis AI")
        self.title_label.setObjectName("title")

        self.status_dot = QLabel()
        self.status_dot.setObjectName("status_dot")
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.hide()

        self.min_button = QPushButton("−")
        self.min_button.setObjectName("min_btn")
        self.min_button.setFixedSize(30, 30)
        self.min_button.setToolTip("Minimizar")
        self.min_button.clicked.connect(self.toggle_minimize)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("close_btn")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setToolTip("Cerrar")
        self.close_button.clicked.connect(self.close)

        title_layout.addWidget(self.ordis_dot)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.status_dot)
        title_layout.addStretch()
        title_layout.addWidget(self.min_button)
        title_layout.addWidget(self.close_button)

        container_layout.addWidget(self.titlebar)

        # ----------------------------------------------------
        # CHAT (scroll de burbujas)
        # ----------------------------------------------------

        self.chat_area = QScrollArea()
        self.chat_area.setObjectName("chat_area")
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QFrame.NoFrame)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 6)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()   # mantiene las burbujas arriba

        self.chat_area.setWidget(self.chat_container)
        container_layout.addWidget(self.chat_area, 1)

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

        self.input_area = QWidget()
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(10, 2, 10, 10)
        input_layout.setSpacing(8)

        self.input = ChatInput()
        self.input.setPlaceholderText("Haz tu pregunta, Operador…")
        self.input.enviar.connect(self.enviar)

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("send")
        self.send_button.setFixedSize(42, 42)
        self.send_button.setToolTip("Enviar (Enter)")
        self.send_button.clicked.connect(self.enviar)

        input_layout.addWidget(self.input, 1)
        input_layout.addWidget(self.send_button)

        container_layout.addWidget(self.input_area)

        # ----------------------------------------------------
        # SOMBRA + LAYOUT PRINCIPAL
        # ----------------------------------------------------

        if SHADOW_ACTIVA:
            sombra = QGraphicsDropShadowEffect(self)
            sombra.setBlurRadius(20)
            sombra.setOffset(0, 4)
            sombra.setColor(QColor(0, 0, 0, 150))
            self.container.setGraphicsEffect(sombra)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(PAD, PAD, PAD, PAD)
        main_layout.addWidget(self.container)

        # ----------------------------------------------------
        # SIZE GRIP
        # ----------------------------------------------------

        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.raise_()

        # ----------------------------------------------------
        # MENSAJE INICIAL
        # ----------------------------------------------------

        self._add_burbuja_md("bubble_ai", SALUDO)

    # ========================================================
    # MENSAJES
    # ========================================================

    def _max_bubble_width(self):
        vp = self.chat_area.viewport().width()
        return max(160, int(vp * 0.82))

    def _envolver(self, bubble, derecha):
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(0)
        if derecha:
            row_lay.addStretch(1)
            row_lay.addWidget(bubble)
        else:
            row_lay.addWidget(bubble)
            row_lay.addStretch(1)
        return row

    def _add_burbuja_md(self, tipo, texto):
        browser = BubbleBrowser()
        self._bubbles.append(browser)
        browser.set_max_width(self._max_bubble_width())
        browser.set_markdown(texto)

        bubble = QWidget()
        bubble.setObjectName(tipo)
        bubble_lay = QVBoxLayout(bubble)
        bubble_lay.setContentsMargins(12, 8, 12, 8)
        bubble_lay.addWidget(browser)

        row = self._envolver(bubble, derecha=(tipo == "bubble_user"))
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        QTimer.singleShot(0, self._scroll_abajo)

    def _mostrar_escribiendo(self):
        label = QLabel("Ordis está buscando")
        label.setObjectName("typing_label")

        bubble = QWidget()
        bubble.setObjectName("bubble_ai")
        bubble_lay = QVBoxLayout(bubble)
        bubble_lay.setContentsMargins(14, 9, 14, 9)
        bubble_lay.addWidget(label)

        row = self._envolver(bubble, derecha=False)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)

        self._typing_row = row
        self._typing_label = label
        self._puntos = 0
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(450)
        self._typing_timer.timeout.connect(self._animar_puntos)
        self._typing_timer.start()
        QTimer.singleShot(0, self._scroll_abajo)

    def _animar_puntos(self):
        self._puntos = (self._puntos + 1) % 4
        if self._typing_label:
            self._typing_label.setText("Ordis está buscando" + "." * self._puntos)

    def _quitar_escribiendo(self):
        if self._typing_timer:
            self._typing_timer.stop()
            self._typing_timer.deleteLater()
            self._typing_timer = None
        if self._typing_row:
            self.chat_layout.removeWidget(self._typing_row)
            self._typing_row.deleteLater()
            self._typing_row = None
        self._typing_label = None

    # ========================================================
    # SCROLL
    # ========================================================

    def _scroll_abajo(self):
        sb = self.chat_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _esta_abajo(self):
        sb = self.chat_area.verticalScrollBar()
        return sb.value() >= sb.maximum() - 4

    def _update_bubble_widths(self):
        max_w = self._max_bubble_width()
        for b in self._bubbles:
            b.set_max_width(max_w)
        if self._esta_abajo():
            QTimer.singleShot(0, self._scroll_abajo)

    # ========================================================
    # ENVIAR / RECIBIR
    # ========================================================

    def enviar(self):
        if self._animando or self.minimized:
            return
        if self.worker and self.worker.isRunning():
            return
        pregunta = self.input.toPlainText().strip()
        if not pregunta:
            return

        self.input.clear()
        self._add_burbuja_md("bubble_user", pregunta)
        self._mostrar_escribiendo()
        self._set_espera(True)

        self.worker = Worker(pregunta)
        self.worker.respuesta_lista.connect(self.recibir_respuesta)
        self.worker.error.connect(self.recibir_error)
        self.worker.finished.connect(self._worker_terminado)
        self.worker.start()

    def _worker_terminado(self):
        self.worker = None

    def _set_espera(self, esperando):
        self.input.setEnabled(not esperando)
        self.send_button.setEnabled(not esperando)
        if not esperando:
            self.input.setFocus()

    def recibir_respuesta(self, respuesta):
        self._quitar_escribiendo()
        self._add_burbuja_md("bubble_ai", respuesta)
        self._set_espera(False)
        if self.minimized:
            self.status_dot.show()

    def recibir_error(self, error):
        self._quitar_escribiendo()
        self._add_burbuja_md("bubble_error", f"**Error**\n\n{error}")
        self._set_espera(False)
        if self.minimized:
            self.status_dot.show()

    # ========================================================
    # MINIMIZAR / RESTAURAR (píldora en esquina inferior derecha)
    # ========================================================

    def toggle_minimize(self):
        if self._animando:
            return
        if self.minimized:
            self._restaurar()
        else:
            self._minimizar()

    def _pos_anclada(self, size):
        """Posición de la ventana (de tamaño `size`) anclada abajo-derecha."""
        scr = self.screen() or QGuiApplication.primaryScreen()
        avail = scr.availableGeometry()
        x = avail.left() + avail.width() - SNAP_MARGIN - size.width() + PAD
        y = avail.top() + avail.height() - SNAP_MARGIN - size.height() + PAD
        return QPoint(x, y)

    def _pill_geometry(self):
        size = QSize(PILL_W + 2 * PAD, PILL_H + 2 * PAD)
        return QRect(self._pos_anclada(size), size)

    def _minimizar(self):
        self._animando = True
        self.minimized = True
        self._geometria_previa = self.geometry()

        self.chat_area.hide()
        self.input_area.hide()
        self.size_grip.hide()
        self.min_button.hide()
        self.close_button.hide()

        destino = self._pill_geometry()
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(280)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(self.geometry())
        anim.setEndValue(destino)
        anim.finished.connect(lambda: self._fin_minimizar(destino))
        self._anim = anim
        anim.start()

    def _fin_minimizar(self, destino):
        self.titlebar.setFixedHeight(PILL_H)
        self.container.setObjectName("pill_container")
        self.titlebar.setObjectName("pill_titlebar")
        self._repolish(self.container, self.titlebar)
        self.setMinimumSize(destino.size())
        self.setMaximumSize(destino.size())
        self.setCursor(Qt.PointingHandCursor)
        self._animando = False

    def _restaurar(self):
        self._animando = True
        self.minimized = False
        self.status_dot.hide()
        self.setCursor(Qt.ArrowCursor)

        self.titlebar.setFixedHeight(TITLE_H)
        self.container.setObjectName("container")
        self.titlebar.setObjectName("titlebar")
        self._repolish(self.container, self.titlebar)
        self.setMinimumSize(1, 1)
        self.setMaximumSize(16777215, 16777215)

        destino = self._geometria_previa or QRect(QPoint(80, 80), QSize(560, 720))
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(280)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(self.geometry())
        anim.setEndValue(destino)
        anim.finished.connect(self._fin_restaurar)
        self._anim = anim
        anim.start()

    def _fin_restaurar(self):
        self.chat_area.show()
        self.input_area.show()
        self.size_grip.show()
        self.min_button.show()
        self.close_button.show()
        self.setMinimumSize(WIN_MIN_W, WIN_MIN_H)
        self._update_bubble_widths()
        QTimer.singleShot(0, self._scroll_abajo)
        self.input.setFocus()
        self._animando = False

    def _repolish(self, *widgets):
        for w in widgets:
            w.style().unpolish(w)
            w.style().polish(w)

    # ========================================================
    # IMANTAR A BORDES
    # ========================================================

    def _snap_pos(self, pos):
        scr = self.screen() or QGuiApplication.primaryScreen()
        if not scr:
            return None
        avail = scr.availableGeometry()
        x_right = avail.left() + avail.width()
        y_bottom = avail.top() + avail.height()

        # aristas visibles (sin el pad de la sombra)
        cont_izq = pos.x() + PAD
        cont_der = pos.x() + self.width() - PAD
        cont_arr = pos.y() + PAD
        cont_aba = pos.y() + self.height() - PAD

        x, y = pos.x(), pos.y()

        d_izq = cont_izq - (avail.left() + SNAP_MARGIN)
        d_der = (x_right - SNAP_MARGIN) - cont_der
        if abs(d_izq) <= SNAP_THRESHOLD:
            x = avail.left() + SNAP_MARGIN - PAD
        elif abs(d_der) <= SNAP_THRESHOLD:
            x = x_right - SNAP_MARGIN - self.width() + PAD

        d_arr = cont_arr - (avail.top() + SNAP_MARGIN)
        d_aba = (y_bottom - SNAP_MARGIN) - cont_aba
        if abs(d_arr) <= SNAP_THRESHOLD:
            y = avail.top() + SNAP_MARGIN - PAD
        elif abs(d_aba) <= SNAP_THRESHOLD:
            y = y_bottom - SNAP_MARGIN - self.height() + PAD

        if (x, y) == (pos.x(), pos.y()):
            return None
        return QPoint(x, y)

    def _animar_pos(self, destino):
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setEndValue(destino)
        self._anim = anim
        anim.start()

    # ========================================================
    # ARRASTRAR / CLIC EN LA PÍLDORA
    # ========================================================

    def mousePressEvent(self, event):
        if self._animando:
            return

        # Píldora: clic en cualquier parte = expandir
        if self.minimized:
            p = event.position()
            dentro = (
                PAD <= p.x() <= self.width() - PAD
                and PAD <= p.y() <= self.height() - PAD
            )
            if dentro and event.button() == Qt.LeftButton:
                self.toggle_minimize()
            return

        # Normal: arrastrar desde la barra de título
        if event.button() == Qt.LeftButton:
            p = event.position()
            en_titulo = (
                PAD <= p.x() <= self.width() - PAD
                and p.y() <= TITLE_H + PAD
            )
            if en_titulo:
                self.drag_position = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
                )
                event.accept()

    def mouseMoveEvent(self, event):
        if self._animando or self.minimized:
            return
        if (
            event.buttons() & Qt.LeftButton
            and not self.drag_position.isNull()
        ):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if not self.drag_position.isNull():
            self.drag_position = QPoint()
            destino = self._snap_pos(self.pos())
            if destino:
                self._animar_pos(destino)
        event.accept()

    # ========================================================
    # EVENTOS DE VENTANA
    # ========================================================

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.size_grip.move(
            self.width() - PAD - 18,
            self.height() - PAD - 18,
        )
        if not self.minimized:
            self._update_bubble_widths()

    def showEvent(self, event):
        super().showEvent(event)
        if self._primera_vez:
            self._primera_vez = False
            self.move(self._pos_anclada(self.size()))
            QTimer.singleShot(0, self._tras_mostrar)

    def _tras_mostrar(self):
        self._update_bubble_widths()
        self._scroll_abajo()
        self.input.setFocus()

    def closeEvent(self, event):
        if self._typing_timer:
            self._typing_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(1000)
        event.accept()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = ChatWindow()
    window.show()

    sys.exit(app.exec())