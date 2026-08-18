import reflex as rx


class ItemState(rx.State):
    items: list[str] = []

    def load_items(self):
        self.items = [
            "Produto 1",
            "Produto 2",
            "Produto 3",
        ]


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Stock Predict"),
            rx.button(
                "Carregar Itens",
                on_click=ItemState.load_items,
            ),
            rx.foreach(
                ItemState.items,
                lambda item: rx.text(item),
            )
        ),
        height="100vh",
    )


app = rx.App()
app.add_page(index)
