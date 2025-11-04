from PySide6.QtCore import QPropertyAnimation, QPoint, QEasingCurve, QRect

class Animator:
    """A collection of static methods for applying animations to widgets."""
    
    @staticmethod
    def apply_push_animation(widget):
        """Applies a 'push' effect to a widget on click."""
        def on_press():
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(100)
            anim.setStartValue(widget.pos())
            anim.setEndValue(widget.pos() + QPoint(2, 2))
            anim.start()

        def on_release():
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(100)
            anim.setStartValue(widget.pos())
            anim.setEndValue(widget.pos() - QPoint(2, 2))
            anim.start()
        
        widget.pressed.connect(on_press)
        widget.released.connect(on_release)

    @staticmethod
    def apply_morph_animation(widget):
        """Applies a 'morph' (shrink and grow) effect on click."""
        def on_click():
            start_geo = widget.geometry()
            
            anim_shrink = QPropertyAnimation(widget, b"geometry")
            end_geo_shrink = QRect(start_geo.x() + 10, start_geo.y() + 5, start_geo.width() - 20, start_geo.height() - 10)
            anim_shrink.setDuration(150)
            anim_shrink.setStartValue(start_geo)
            anim_shrink.setEndValue(end_geo_shrink)
            anim_shrink.setEasingCurve(QEasingCurve.InOutQuad)
            
            anim_grow = QPropertyAnimation(widget, b"geometry")
            anim_grow.setDuration(150)
            anim_grow.setStartValue(end_geo_shrink)
            anim_grow.setEndValue(start_geo)
            anim_grow.setEasingCurve(QEasingCurve.OutBounce)

            anim_shrink.finished.connect(anim_grow.start)
            anim_shrink.start()

        widget.clicked.connect(on_click)

