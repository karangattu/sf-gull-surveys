import ipyleaflet as L
import pandas as pd
from pathlib import Path
from htmltools import css
from shiny import App, reactive, render, req, ui
from shinywidgets import output_widget, register_widget, render_widget
import plotly.express as px
from shiny.types import ImgData
from ipywidgets import Layout
import plotly.graph_objects as go


app_ui = ui.page_fluid(
    ui.row(
        ui.column(1, ui.output_image("logo", inline=True)),
        ui.column(
            10, ui.h3("California Gull Nest Surveys in SF Bay Area", align="center")
        ),
    ),
    output_widget("map"),
    ui.row(
        ui.column(
            1, ui.input_action_button("reset", "Reset", class_="btn-secondary")
        ),
        ui.column(
            6,
            ui.h4(
                "Click on any gull colony location to see the graph below",
                align="center",
            ),
        ),
        ui.input_select(
            "type",
            label="Graph type",
            choices=[
                "Total number of nests",
                "empty nests",
                "1 egg nests",
                "2 egg nests",
                "3 egg nests",
                "4 egg nests",
            ],
        ),
        style=css(
            display="flex",
            justify_content="center",
            align_items="center",
            gap="2rem",
        ),
    ),
    ui.div(
        output_widget("graph_widget"),
    ),
)


def server(input, output, session):
    @output
    @render.image
    def logo():
        from pathlib import Path

        dir = Path(__file__).resolve().parent
        img: ImgData = {"src": str(dir / "sfbbo_logo.png"), "width": "100px"}
        return img

    @output
    @render_widget
    def graph_widget():
        # use plotly graph objects to create a filled graph since plotly express does not support gaps in graphs
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=bird_data()["Year"],
                y=bird_data()[input.type()],
                text=f"{input.type()} in {bird_selected.get()} colony",
                mode="lines+markers",
                connectgaps=False,
                marker=dict(size=5, line=dict(width=5, color="darkblue")),
                line=dict(shape="spline", width=5, color="peru"),
                # fill="tonexty",
            )
        )

        # Configure the layout
        fig.update_layout(
            title=f"{input.type()} in {bird_selected.get()} colony",
            xaxis=dict(title="Year", title_font=dict(size=22), tickfont=dict(size=20)),
            yaxis=dict(
                title=input.type(), title_font=dict(size=22), tickfont=dict(size=20)
            ),
            plot_bgcolor="whitesmoke",
        )
        fig.update_layout(modebar_remove=["autoScale2d", "autoscale", "editInChartStudio", "editinchartstudio", "hoverCompareCartesian", "hovercompare", "lasso", "lasso2d", "orbitRotation", "orbitrotation", "pan", "pan2d", "pan3d", "reset", "resetCameraDefault3d", "resetCameraLastSave3d", "resetGeo", "resetSankeyGroup", "resetScale2d", "resetViewMapbox", "resetViews", "resetcameradefault", "resetcameralastsave", "resetsankeygroup", "resetscale", "resetview", "resetviews", "select", "select2d", "sendDataToCloud", "senddatatocloud", "tableRotation", "tablerotation", "toImage", "toggleHover", "toggleSpikelines", "togglehover", "togglespikelines", "toimage", "zoom", "zoom2d", "zoom3d", "zoomIn2d", "zoomInGeo", "zoomInMapbox", "zoomOut2d", "zoomOutGeo", "zoomOutMapbox", "zoomin", "zoomout"])
        return fig

    def read_csv_file():
        infile = Path(__file__).parent / "bird_surveys.csv"
        df = pd.read_csv(infile)
        return df

    def initialize_map():
        return L.Map(
            center=(37.495605832194876, -122.08810091916739),
            min_zoom=12,
            max_zoom=16,
            zoom=12,
            scroll_wheel_zoom=True,
            close_popup_on_click=False,
            basemap=L.basemaps.Esri.WorldImagery,
            layout=Layout(height="550px"),
        )

    def create_icon():
        return L.Icon(
            icon_url="https://cdn-icons-png.flaticon.com/512/7451/7451013.png",
            icon_size=[64, 64],
            shadow_size=[32, 32],
            shadow_url="https://cdn-icons-png.flaticon.com/512/427/427432.png",
            shadow_anchor=[38, 1],
        )

    # Create a reactive value to store the map click location
    map_click_value = reactive.Value(None)
    bird_selected = reactive.Value(None)
    df = read_csv_file()
    icon = create_icon()
    map = initialize_map()

    def marker_row(index, row):
        marker = L.Marker(
            location=(row["Latitude"], row["Longitude"]),
            icon=icon,
            draggable=False,
            title=row["Survey Location"],
        )

        def _on_click(**kwargs):
            map_click_value.set(f"Clicked on {marker.title}")
            map.center = marker.location
            map.zoom = 16
            bird_selected.set(row["Survey Location"])

        def _mouse_over(**kwargs):
            map_click_value.set(f"Hover over {marker.title}")

        marker.on_click(_on_click)
        marker.on_mouseover(_mouse_over)
        map.add_layer(marker)

    for index, row in df.iterrows():
        marker_row(index, row)
    map.add_control(L.leaflet.ScaleControl(position="bottomleft"))
    register_widget("map", map)

    @reactive.Calc
    def bird_data():
        req(bird_selected.get())
        return df[df["Survey Location"] == bird_selected.get()]

    @reactive.Effect
    @reactive.event(input.reset)
    def _reset_map():
        map.center = [37.495605832194876, -122.08810091916739]
        map.zoom = 11
        bird_selected.set(None)


app = App(app_ui, server)
