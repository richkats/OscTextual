from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from rich_pixels import Pixels
from PIL import Image

from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio


ip = "0.0.0.0"
port = 42042

class MainWidget(Widget):

    title = reactive("No song")
    odd_tick = reactive(False)
    image_path = reactive(None)

    @staticmethod
    def drop_image_path(func):
        def wrapper(*args, **kwargs):
            self = args[0]
            self.image_path = None
            return func(*args, **kwargs)
        return wrapper


    def image_render(self): # TODO: Кешировать изображения в памяти (возможно не надо)
        with Image.open(self.image_path) as image:
            # image = image.resize((100, 56))
            image = image.resize((100, 100))
            return Pixels.from_image(image)


    def image_handler(self, address, *args):
        self.image_path = "img/" + args[0]
        self.render()

    @drop_image_path
    def title_handler(self, address, *args):
        self.title = args[0]
        self.render()

    @drop_image_path
    def tick_handler(self, address, *args):
        self.odd_tick = not self.odd_tick
        self.styles.background = "black" if self.odd_tick else "red"

    @drop_image_path
    def change_color_handler(self, address, *args):
        match len(args):
            case 1:
                self.styles.background = args[0]
            case 2:
                self.styles.background = args[0]
                self.styles.color = args[1]


    def render(self) -> str | Pixels:
        return f"{self.title}" if self.image_path is None else self.image_render()


class WatchApp(App):
    CSS_PATH = "style.tcss"

    async def init_osc(self):
        dispatcher = Dispatcher()
        main_widget = self.query_one(MainWidget)
        dispatcher.map("/title", main_widget.title_handler)
        dispatcher.map("/tick", main_widget.tick_handler)
        dispatcher.map("/color", main_widget.change_color_handler)
        dispatcher.map("/image", main_widget.image_handler)

        loop = asyncio.get_running_loop()

        server = AsyncIOOSCUDPServer((ip, port), dispatcher, loop)
        transport, protocol = await server.create_serve_endpoint()
        self.notify("Server started")

    def compose(self) -> ComposeResult:
        yield MainWidget()

    def on_mount(self) -> None:
        self.run_worker(self.init_osc())

if __name__ == "__main__":
    app = WatchApp()
    app.run()
