import json

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.textinput import TextInput

from backend import (auto_detect_loc, check_internet, get_weather_data,
                     unit_converter, create_necessary_files)

Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '400')

# Making a backend check to create a settings JSON file
create_necessary_files()


# Setting up a custom class to manage a settings icon that's also a button
class ImageButton(ButtonBehavior, Image):
    pressed = 0

    def __init__(self, butt_type=None, curr_city=None, **kwargs):
        super().__init__(**kwargs)

        self.butt_type = butt_type
        # curr_city is used to check for favorite places
        self.curr_city = curr_city

        self.star_on = "weather_pictures/star_on.png"
        self.star_off = "weather_pictures/star_off.png"

        if self.butt_type == "settings":
            self.source = "weather_pictures/settings_icon.png"
            self.size_hint = (None, None)
            self.size = (50, 50)

        elif self.butt_type == "star":
            self.show_star()

        else:
            self.show_checkbox()

    # The two similar methods below are solely used for the purposes of showing the checkbox and star 
    # button in the correct state (checked/unchecked or on/off)
    def show_star(self):
        self.favorites = json.load(open("favorites.json"))

        if self.curr_city in self.favorites["favorite_places"]:
            self.source = self.star_on
        else:
            self.source = self.star_off

        self.size_hint = (None, None)
        self.size = (50, 50)

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

            popup = Popup(title="Settings", size_hint=(None, None),
                          size=(350, 200), content=popup_layout)
            popup.open()

        else:
            self.toggle()

    def toggle(self):
        """
        This method reads the JSON files available to know the state of how the settings are. It then toggles the checkbox or star button appropriately
        """
        if self.butt_type == "star":
            data_to_write = {"favorite_places": self.favorites["favorite_places"]}

            if self.source == self.star_on:
                self.source = self.star_off
                data_to_write["favorite_places"].remove(self.curr_city)
            else:
                self.source = self.star_on
                data_to_write["favorite_places"].append(self.curr_city)

            json.dump(data_to_write, open("favorites.json", "w"))
        
        else:
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
        self.submit.bind(on_press=lambda x:self.info_checker(city=self.inside.city.text, country=self.inside.country.text))
        self.add_widget(self.submit)

        self.auto_detect = Button(
            text="Detect your location", font_size=30, size_hint=(1.2, 0.5))
        self.auto_detect.bind(
            on_press=lambda x: self.info_checker(auto_detect=True, city=self.inside.city.text, country=self.inside.country.text))
        self.add_widget(self.auto_detect)

        self.favorites = Button(text="Favorite cities", font_size=30, size_hint=(0.8, 0.3), on_press=self.go_to_fav_screen)
        self.add_widget(self.favorites)

    def go_to_fav_screen(self, instance):
        weather_app.favorites_page.show_faves()
        weather_app.screen_manager.current = "Favorites Page"

    def get_weather_info(self, check_type="manual", city="", country=""):
        # Reading unit data
        settings_data = json.load(open("settings.json"))
        unit = "imperial" if not settings_data["use_celsius"] else "metric"
        symbol = "F" if not settings_data["use_celsius"] else "C"
        
        if check_type == "auto":
            data = auto_detect_loc(unit, symbol)
            print(data)
        else:
            data = get_weather_data(
                city, unit=unit, country=country, symbol=symbol)
            if data == None:
                self.handle_error()
                weather_app.screen_manager.current = "Input Page"
            print(data)

        if data != None:
            weather_app.weather_page.decorate_page(data)
            self.go_to_weather_screen()

    def go_to_weather_screen(self):
        weather_app.screen_manager.current = "Weather Page"

    def info_checker(self, city, country="", instance=None, auto_detect=False):
        """This method will check for any flaws in the input data and also checks if an internet connection is present"""
        if check_internet():
            if auto_detect:
                self.go_to_loading_screen()
                Clock.schedule_once(lambda x: self.get_weather_info(
                    check_type="auto", city=city, country=country), 0.8)
            else:
                if city == "":
                    self.handle_error(err_type="missing data")
                else:
                    self.go_to_loading_screen()

                    Clock.schedule_once(lambda x: self.get_weather_info(
                        check_type="manual", city=city, country=country), 0.8)

        else:
            print("No internet connection present")
            self.handle_error(err_type="no connection")

            weather_app.favorites_page.update_remove_widgets()

    def go_to_loading_screen(self):
        weather_app.screen_manager.current = "Loading Page"

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


class LoadingScreen(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1

        self.loading_text = Label(text="Loading...", font_size=23)
        self.add_widget(self.loading_text)


class FavoritesScreen(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1

        # A lookout variable to know if widgets on the favorites screen are to be cleared or not
        self.remove_widgets = ""
    
    def show_faves(self):
        self.favorites = json.load(open("favorites.json"))

        layout = GridLayout(cols=1, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        for place in self.favorites["favorite_places"]:
            layout.add_widget(Button(text=place, on_press=self.process_fave, size_hint_y=None, height=90))

        layout.add_widget(Button(text="Go back", on_press=self.back, size_hint_y=None, height=90))

        root = ScrollView(size_hint=(1, None), size=(500, 400))
        root.add_widget(layout)
        
        self.add_widget(root)

    def back(self, instance):
        weather_app.screen_manager.current = "Input Page"
        Clock.schedule_once(lambda x: self.clear_widgets(), 0.8)

    def update_remove_widgets(self):
        self.remove_widgets = True

    def process_fave(self, instance):
        city = instance.text.split(",")[0]
        country = instance.text.split(",")[-1].strip()

        weather_app.input_page.info_checker(city=city, country=country)

        if not self.remove_widgets:
            Clock.schedule_once(lambda x: self.clear_widgets(), 0.8)


class WeatherScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def decorate_page(self, data):
        self.city, self.country, self.temp, self.humidity, self.rain, self.snow, self.description, self.time, self.time_state, self.symbol = data

        self.inside = GridLayout()
        self.inside.rows = 4
        self.inside.cols = 1

        self.toolbar_layout = GridLayout(cols=2)
        self.settings_button = ImageButton(butt_type="settings")
        self.toolbar_layout.add_widget(self.settings_button)
    
        self.star_button = ImageButton(butt_type="star", curr_city=f"{self.city}, {self.country}")
        self.toolbar_layout.add_widget(self.star_button)

        self.inside.add_widget(self.toolbar_layout)

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

        self.loading_page = LoadingScreen()
        screen = Screen(name="Loading Page")
        screen.add_widget(self.loading_page)
        self.screen_manager.add_widget(screen)

        self.favorites_page = FavoritesScreen()
        screen = Screen(name="Favorites Page")
        screen.add_widget(self.favorites_page)
        self.screen_manager.add_widget(screen)


        return self.screen_manager


if __name__ == "__main__":
    weather_app = MyApp()
    weather_app.run()
