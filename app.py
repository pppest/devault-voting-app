from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
import json
import voteutils

voteutils.has_config()
voting_addresses = voteutils.get_voting_addresses()
proposals_online = voteutils.get_online_proposals()
selected_proposals = []
selected_addresses = []

# get main layout
with open("awedevotl.kv", "r") as f:
    mainkv = f.read()



class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    pass
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabelProposals(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabelProposals, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabelProposals, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            selected_proposals.append(rv.data[index]['text'])
            print("Selected proposal changed to {0}".format(rv.data[index]))
            print(selected_proposals)
        else:
            if rv.data[index]['text'] in selected_proposals:
                selected_proposals.remove(rv.data[index]['text'])
            print("Selected proposal removed for {0}".format(rv.data[index]))
            print(selected_proposals)

class SelectableLabelAddresses(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabelAddresses, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabelAddresses, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            selected_addresses.append(rv.data[index]['text'])
            print("Selected address changed to {0}".format(rv.data[index]))
            print(selected_addresses)
        else:
            if rv.data[index]['text'] in selected_addresses:
                selected_addresses.remove(rv.data[index]['text'])
            print("Selected address removed for {0}".format(rv.data[index]))
            print(selected_addresses)



class CoverScreen(Screen):
    def __init__(self, **kwargs):
        super(CoverScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.goto_userinfo, 3)

    def goto_userinfo(self,dt):
        self.manager.current = 'userinfoscreen'



class UserInfoScreen(Screen):
    pass


class Voter(ScreenManager):
    pass



# add proposals list
class RV_proposals(RecycleView):
    def __init__(self, **kwargs):
        super(RV_proposals, self).__init__(**kwargs)
        self.data = [{'text': str(p)} for p in proposals_online]
        print('in p rv')

# add address list
class RV_addresses(RecycleView):
    def __init__(self, **kwargs):
        super(RV_addresses, self).__init__(**kwargs)
        self.data = [{'text': str(a)} for a in voting_addresses]
        print('in a rv')


votingapp = Builder.load_string(mainkv)


class App(App):

    # voting
    def vote(self, vote_value, walletpass, username, userpassword, **kwargs):
        global selected_proposals
        global selected_addresses
        global voteutils

        # check for selection
        if selected_proposals == []:
            self.root.ids.output.text += "\nno proposal selected"
            return
        elif selected_addresses == []:
            self.root.ids.output.text += "\nno address selected"
            return

        #start voting process
        self.root.ids.output.text+="\nvoting..."
        #unlock wallet
        self.root.ids.output.text += "\nunlocking wallet..."
        if voteutils.unlock_wallet(walletpass,10*(len(selected_addresses)+len(selected_proposals))) != 0:
            self.root.ids.output.text += "\nwallet passphrase wrong"
            return
        self.root.ids.output.text += "\nwallet unlocked for " + str(10*(len(selected_addresses)+len(selected_proposals))) + " seconds"

        # login to devault.online account
        self.root.ids.output.text += "\nloggin in to devault.online"
        session =voteutils.login(username,userpassword)

        # for each proposal selected\
        for p in selected_proposals:
            print('proposal: ', p)
            self.root.ids.output.text += "\n" + 'voting for proposal: ' + vote_value
            # get vkey
            vkey = voteutils.get_verification_key(session, p, vote_value)
            print('verification key: ', vkey)
            self.root.ids.output.text += "\n" + 'verification key: ' + vkey
            # for each adderss selected
            for a in selected_addresses:
                #vote
                print(a)
                a = a.replace("'",'"')
                addy = json.loads(a)
                print(a[0])
                signature = voteutils.sign_vote(addy[0], vkey)
                print(signature)
                self.root.ids.output.text += "\n" + signature
                posted = voteutils.post_vote(session, p, vote_value, a, signature)
                self.root.ids.output.text += "\n" + str(posted)
                print(posted)

        self.root.ids.output.text += "\nvoting finished"
        voteutils.lock_wallet()
        self.root.ids.output.text += "\nwallet locked"

        return

    def build(self):
        return votingapp

    def clear(self):
        global selected_proposals
        global selected_addresses
        # clear selection
        selected_proposals = []
        selected_addresses = []
        return "cleared"


if __name__ == '__main__':
    App().run()