import json

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput

from backend import auto_detect_loc, check_internet, get_weather_data, unit_converter

Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '400')

#TODO: Add a simple script in the beginnig to create the settings.json file
#TODO: Add a loading screen to add a visual effect while the app make API calls to show weather info
#TODO: Implement a "Favorite Places" feature where users can add their favorite cities for quick access


# Setting up a custom class to manage a settings icon that's also a button
class ImageButton(ButtonBehavior, Image):
    pressed = 0

    def __init__(self, butt_type=None, **kwargs):
        super().__init__(**kwargs)
        
        self.butt_type = butt_type

        if self.butt_type == "settings":
            self.source = "weather_pictures/settings_icon.png"
            self.size_hint= (None, None)
            self.size = (50, 50)
            self.pos_hint = (None, None)
            self.pos = (150, 150)

        elif self.butt_type == "checkbox":
            self.show_checkbox()

    # This method is called the first time the checkbox is to be shown
    # Therefore it reads the JSON file to show the checkbox appropriately
    def show_checkbox(self):
        self.settings_data = json.load(open("settings.json"))

        if self.settings_data["use_celsius"]:
            self.source = "atlas://data/images/defaulttheme/checkbox_on"
        else:
            self.source = "atlas://data/images/defaulttheme/checkbox_off"

    def on_press(self):
        if self.butt_type == "settings":
            popup_layout = GridLayout(cols=2, rows=2)

            self.msg_to_display = Label(text="Use Celsius")
            popup_layout.add_widget(self.msg_to_display)

            self.unit_checkbox = ImageButton("checkbox")
            popup_layout.add_widget(self.unit_checkbox)

            popup = Popup(title="Settings", size_hint=(None, None), size=(350, 200), content=popup_layout)
            popup.open()

        else:
            self.toggle()

    # This method again reads the JSON file which might look redundant but it is to keep in mind
    # that this method is to be called every the checkbox if clicked so it is important to read and write to JSON
    # file regardless of if the JSON is already read before
    def toggle(self):
        self.settings_data = json.load(open("settings.json"))

        data = {"use_celsius": ""}
        if self.settings_data["use_celsius"]:
            do = "off"
            data["use_celsius"] = False
            weather_app.weather_page.update_temp_now("metric")
        else:
            do = "on"
            data["use_celsius"] = True
            weather_app.weather_page.update_temp_now("imperial")
        
        json.dump(data, open("settings.json", "w"))
        self.source = f"atlas://data/images/defaulttheme/checkbox_{do}"


class InputScreen(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1

        self.inside = GridLayout()
        self.inside.cols = 2

        self.inside.city_label = Label(text="Enter the name of the city")
        self.inside.add_widget(self.inside.city_label)

        self.inside.city = TextInput(multiline=False)
        self.inside.add_widget(self.inside.city)

        self.inside.country_label = Label(
            text="Enter the country for better accuracy")
        self.inside.add_widget(self.inside.country_label)

        self.inside.country = TextInput(multiline=False)
        self.inside.add_widget(self.inside.country)

        self.add_widget(self.inside)

        self.submit = Button(text="Enter", font_size=30, size_hint=(1.2, 0.5))
        self.submit.bind(on_press=lambda x: self.get_weather_info(
            city=self.inside.city.text, country=self.inside.country.text))
        self.add_widget(self.submit)

        self.auto_detect = Button(
            text="Detect your location", font_size=30, size_hint=(1.2, 0.5))
        self.auto_detect.bind(
            on_press=lambda x: self.get_weather_info(check_type="auto"))
        self.add_widget(self.auto_detect)

    def get_weather_info(self, check_type="manual", city="", country=""):
        if check_internet():
            # Reading unit data
            settings_data = json.load(open("settings.json"))
            unit = "imperial" if not settings_data["use_celsius"] else "metric"
            symbol = "F" if not settings_data["use_celsius"] else "C"
            if check_type == "auto":
                data = auto_detect_loc(unit, symbol)
                print(data)
            else:
                data = get_weather_data(city, unit=unit, country=country, symbol=symbol)
                if data == None:
                    self.handle_error()
                print(data)
            if data != None:
                weather_app.weather_page.decorate_page(data)
                self.go_to_weather_screen()
        else:
            print("No internet connection present")
            self.handle_error(err_type="no connection")

    def go_to_weather_screen(self):
        weather_app.screen_manager.current = "Weather Page"

    def handle_error(self, err_type="missing data"):
        self.inside.city.text = ""
        self.inside.country.text = ""

        if err_type == "missing data":
            popup = Popup(title="City not found error", content=Label(
                text="The entered data didn't match any places", color=[1, 0, 0, 1]), size_hint=(0.6, 0.2))
        elif err_type == "no connection":
            popup = Popup(title="No Internet Connection", content=Label(
                text="You currently don't have any internet connection. Try again later", color=[1, 0, 0, 1]), size_hint=(1.0, 0.2))

        popup.open()


class WeatherScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def decorate_page(self, data):
        self.city, self.country, self.temp, self.humidity, self.rain, self.snow, self.description, self.time, self.time_state, self.symbol = data

        self.inside = GridLayout()
        self.inside.rows = 4
        
        self.settings_button = ImageButton(butt_type="settings")
        self.inside.add_widget(self.settings_button)

        if self.time_state == "Day":
            color = [0, 0, 0, 1]
        elif self.time_state == "Night":
            color = [1, 1, 1, 1]

        # First row, city and country info
        self.inside.info_label = Label(text=f"{self.city}, {self.country}", color=[
                                       0, 0, 0, 1] if self.description == "haze" else color, font_size="23sp")
        self.inside.add_widget(self.inside.info_label)

        # Second row, temperature
        self.inside.temp_label = Label(
            text=f"{self.temp} °{self.symbol}", color=color, font_size="63sp")
        self.inside.add_widget(self.inside.temp_label)

        self.inside.extra_info_description = Label(
            text=f"{self.description}", color=color, font_size="23sp")
        self.inside.add_widget(self.inside.extra_info_description)

        self.back = Button(text="Go back")
        self.back.bind(on_press=self.back_to_main)
        self.add_widget(self.back)

        self.handle_bg_pic()

        self.add_widget(self.inside)

    def update_temp_now(self, unit):
        value, symbol = unit_converter(self.temp, unit)
        self.inside.temp_label.text = f"{value} °{symbol}"

        self.temp = value

    def handle_bg_pic(self):
        """A method to handle the background picture of the weather screen depending on how the weather is"""
        if self.time_state == "Day":
            if "snow" in self.description:
                self.add_widget(Image(source="weather_pictures/day_snow.jpg"))
            elif "rain" in self.description or "drizzle" in self.description:
                self.add_widget(
                    Image(source="weather_pictures/day_raining.jpg"))
            elif "clear sky" in self.description:
                self.add_widget(
                    Image(source="weather_pictures/day_clear_sky.jpg"))

        elif self.time_state == "Night":
            if "snow" in self.description:
                self.add_widget(
                    Image(source="weather_pictures/night_snow.jpg"))
            elif "rain" in self.description or "drizzle" in self.description:
                self.add_widget(
                    Image(source="weather_pictures/night_raining.jpg"))
            elif "clear sky" in self.description:
                self.add_widget(
                    Image(source="weather_pictures/night_clear_sky.jpg"))

        if "haze" in self.description:
            self.add_widget(Image(source="weather_pictures/haze.jpg"))
        elif "shower" in self.description:
            self.add_widget(Image(source="weather_pictures/showers.jpg"))
        elif "mist" in self.description or "fog" in self.description:
            self.add_widget(Image(source="weather_pictures/mist.jpg"))
        elif "storm" in self.description or "thunder" in self.description:
            self.add_widget(Image(source="weather_pictures/storm.jpg"))
        elif "cloud" in self.description:
            self.add_widget(Image(source="weather_pictures/cloud.jpg"))
        elif "win" in self.description:
            self.add_widget(Image(source="weather_pictures/wind.jpg"))
        elif self.temp >= 75 or "sun" in self.description:
            self.add_widget(Image(source="weather_pictures/hot_day.jpg"))

    def back_to_main(self, instance):
        weather_app.input_page.inside.city.text = ""
        weather_app.input_page.inside.country.text = ""

        weather_app.screen_manager.current = "Input Page"


class MyApp(App):
    def build(self):
        self.title = "Weather App"
        self.icon = "weather_pictures/weather_icon.png"
        self.screen_manager = ScreenManager()

        # Creating all of our screens to show up
        self.input_page = InputScreen()
        screen = Screen(name="Input Page")
        screen.add_widget(self.input_page)
        self.screen_manager.add_widget(screen)

        self.weather_page = WeatherScreen()
        screen = Screen(name="Weather Page")
        screen.add_widget(self.weather_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager


if __name__ == "__main__":
    weather_app = MyApp()
    weather_app.run()
