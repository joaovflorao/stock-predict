import reflex as rx


def nav_bar() -> rx.Component:
    return rx.hstack(
        rx.link("Carregar Dados", href="/ingestion"),
        rx.link("Previsão", href="/"),
        rx.link("Recomendação de Compra", href="/recommendation"),
        rx.link("Oportunidades", href="/opportunities"),
        spacing="4",
        padding_bottom="1em",
    )
