#
#  FLAPPY BIRD DEMO
#

import random
import sys
import threading
import time

from visual import (display, sphere, vector, curve, color,
                    frame, rate, extrusion, shapes, label)

# Frame per second
FPS = 30
DEBUG = False

WINDOW_TITLE = "Flappy Bird Demo"
WINDOW_TITLE_BAR = 20
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650

CANVAS_WIDTH = WINDOW_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT
CANVAS_COLOR = color.black

GROUND_WIDTH = CANVAS_WIDTH
GROUND_HEIGHT = 50
GROUND_COLOR = color.red
GROUND_FILL_COLOR = GROUND_COLOR

TUBE_WIDTH = 100
TUBE_HEIGHT = 100
TUBE_HEIGHT_RANGE = (100, 400)
TUBE_VERTICAL_GAP = 170
TUBE_COLOR = (117.0/256, 190.0/256, 47.0/256)
TUBE_FILL_COLOR = TUBE_COLOR
TUBE_DISTANCE_BETWEEN = 350
TUBE_VELOCITY = 200  # Horizontal pixels per second

BIRD_WIDTH = 50
BIRD_HEIGHT = 50
BIRD_COLOR = color.magenta
BIRD_FLYING_VELOCITY = 250          # Vertical pixels per second
BIRD_FLYING_ACCELERATION = -0.1     # Bird go high speed (percent)
BIRD_FLYING_TIME = 0.4              # seconds
BIRD_FALLING_VELOCITY = 100         # Vertical pixels per second
BIRD_FALLING_ACCELERATION = 0.1     # Bird go low speed (percent)

bird = None
ground = None
tube_mgr = None
main_view = None
collision_detector = None


def log(msg):
    """Logs a message if DEBUG"""
    if DEBUG:
        print(msg)


class Rect(object):
    """A class represents a rectangle can be displayed on screen"""
    def __init__(self, pos, size, color=color.green, fill_color=color.green):
        self.pos = pos
        self.size = size
        self.color = color
        self.fill_color = fill_color
        self.extrude = extrusion(shape=self._create_rect(), color=fill_color)

    def _create_rect(self):
        x, y = self.pos
        w, h = self.size
        return shapes.rectangle(pos=(x+w/2, y+h/2), width=w, height=h)

    def _set(self, pos, size, color, fill_color):
        self.pos = pos
        self.size = size
        self.color = color
        self.fill_color = fill_color

        extrude = self.extrude
        extrude.color = fill_color
        extrude.shape = self._create_rect()

    def set_pos(self, pos):
        self._set(pos, self.size, self.color, self.fill_color)

    def set_size(self, size):
        self._set(self.pos, size, self.color, self.fill_color)

    def set_colors(self, color, fill_color):
        self._set(self.pos, self.size, color, fill_color)

    def move(self, delta):
        self.set_pos((self.pos[0] + delta[0], self.pos[1] + delta[1]))

    def del_obj(self):
        self.extrude.visible = False
        # TODO: how to remove the object completely?
        del self.extrude


class Ground(object):
    """The ground object"""
    def __init__(self, pos=(0, 0), size=(GROUND_WIDTH, GROUND_HEIGHT),
                 color=GROUND_COLOR, fill_color=GROUND_FILL_COLOR):
        self.pos = pos
        self.size = size
        self.rect = Rect(pos=pos, size=size, color=color, fill_color=fill_color)


class Tube(object):
    """The tube object.

    A tube includes 2 parts, a lower tube and an upper tube.
    """
    def __init__(self, index, pos=(0, 0), lower_size=(TUBE_WIDTH, TUBE_HEIGHT),
                 upper_size=(TUBE_WIDTH, TUBE_HEIGHT),
                 color=TUBE_COLOR, fill_color=TUBE_FILL_COLOR):
        self.index = index
        self.pos = list(pos)
        self.lower_size = lower_size
        self.upper_size = upper_size

        # Each tube includes a lower part and a upper part
        self.lower = Rect(pos=pos, size=lower_size,
                          color=color, fill_color=fill_color)
        upper_pos = (pos[0], CANVAS_HEIGHT - upper_size[1])
        self.upper = Rect(pos=upper_pos, size=upper_size,
                          color=color, fill_color=fill_color)

    @property
    def vertical_gap(self):
        """Calculates the vertical gap between lower tube and upper tube"""
        # return CANVAS_HEIGHT - GROUND_HEIGHT - self.lower_size[1] - self.upper_size[1]
        return self.upper.pos[1] - self.lower.pos[1] - self.lower_size[1]

    def move(self, delta_x):
        self.pos = [self.pos[0] + delta_x, self.pos[1]]
        self.lower.move(delta=(delta_x, 0))
        self.upper.move(delta=(delta_x, 0))

    def del_obj(self):
        self.lower.del_obj()
        self.upper.del_obj()


class TubeMgr(object):
    """The tube objects manager."""
    def __init__(self, tubes_distance=TUBE_DISTANCE_BETWEEN):
        self.tubes_distance = tubes_distance
        self.tubes = []

    def first_tube(self):
        if len(self.tubes) > 0:
            return self.tubes[0]
        return None

    def last_tube(self):
        if len(self.tubes) > 0:
            return self.tubes[-1]
        return None

    def random_tube_height(self):
        """Generates a random tube height"""
        return random.randrange(TUBE_HEIGHT_RANGE[0], TUBE_HEIGHT_RANGE[1])

    def add_tubes(self, count=1):
        """Adds one or more tubes to the tail of tube list"""
        log('Adds %d tube(s) to the tail' % count)
        for i in range(count):
            tube_index = 0
            last_tube = self.last_tube()
            if last_tube:
                pos = [last_tube.pos[0] + self.tubes_distance, GROUND_HEIGHT]
                tube_index = last_tube.index + 1
            else:
                pos = [CANVAS_WIDTH, GROUND_HEIGHT]

            lower_h = self.random_tube_height()
            upper_h = CANVAS_HEIGHT - GROUND_HEIGHT - lower_h - TUBE_VERTICAL_GAP

            lower_size = [TUBE_WIDTH, lower_h]
            upper_size = [TUBE_WIDTH, upper_h]
            tube = Tube(index=tube_index, pos=pos,
                        lower_size=lower_size, upper_size=upper_size)
            self.tubes.append(tube)

    def remove_tubes(self, count=1):
        """Removes one or more tubes from the head of the tube list"""
        for i in range(count):
            first_tube = self.first_tube()
            if first_tube:
                log('Removes 1 tube from the head')
                del self.tubes[0]
                first_tube.del_obj()

    def add_tubes_if_missing(self):
        """Adds more tubes to the tail if needs to"""
        last_tube = self.last_tube()
        if not last_tube:
            self.add_tubes(count=5)
        else:
            x, y = last_tube.pos
            w, h = last_tube.lower_size
            if x + w < CANVAS_WIDTH:
                self.add_tubes(count=5)

    def remove_out_of_scene_tubes(self):
        """Removes the heading tubes that went out of the scene"""
        while True:
            first_tube = self.first_tube()
            if not first_tube:
                break
            x, y = first_tube.pos
            w, h = first_tube.lower_size
            if x + w < 0:
                self.remove_tubes()
            else:
                break

    def move_tubes(self, delta_x):
        """Moves all tubes along the ground"""
        for tube in self.tubes:
            tube.move(delta_x)

    def update(self, time):
        self.add_tubes_if_missing()
        self.remove_out_of_scene_tubes()

        pixels_move = time * TUBE_VELOCITY
        self.move_tubes(-pixels_move)

    def reset(self):
        """Removes all tubes"""
        self.remove_tubes(len(self.tubes))


class Bird(object):
    STATUS_N_A = 'N/A'
    STATUS_FALLING = 'falling'
    STATUS_FLYING = 'flying'
    STATUS_HIT_TUBE = 'hit_tube'
    STATUS_HIT_GROUND = 'hit_ground'

    def __init__(self, size=(BIRD_WIDTH, BIRD_HEIGHT),
                 flying_velocity=BIRD_FLYING_VELOCITY,
                 flying_acceleration=BIRD_FLYING_ACCELERATION,
                 falling_velocity=BIRD_FALLING_VELOCITY,
                 falling_acceleration=BIRD_FALLING_ACCELERATION,
                 color=BIRD_COLOR):
        self.size = size
        self.color = color
        self.flying_velocity = flying_velocity
        self.flying_acceleration = flying_acceleration
        self.falling_velocity = falling_velocity
        self.falling_acceleration = falling_acceleration

        # Bird object
        self.sphere = sphere()
        self.sphere.radius = size[0]/2
        self.sphere.color = color

        # Init bird pos and speed
        self.reset()

    def reset(self):
        self.status = self.STATUS_N_A
        self.got_hit = False
        self.flying_time = 0
        self.current_flying_velocity = self.flying_velocity
        self.falling_time = 0
        self.current_falling_velocity = self.falling_velocity

        # Bird is placed at center of scene
        self.pos = [CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2]
        self.sphere.pos = self.pos

    def move(self, delta_y):
        self.pos = [self.pos[0], self.pos[1] + delta_y]
        self.sphere.pos = self.pos

    def inc_speed(self, v, a, dt):
        return v + (a * dt)
    
    def _set_pos_on_ground(self):
        """Corrects bird position on the ground"""
        self.pos = [self.pos[0], ground.pos[1] + ground.size[1] + self.size[1]/2]
        self.sphere.pos = self.pos

    def _set_status(self, status):
        if self.status != status:
            log('New status: %s' % status)
            self.status = status
            self.current_flying_velocity = self.flying_velocity
            self.current_falling_velocity = self.falling_velocity

    def _action_fly(self, time, flap=False):
        self._set_status(self.STATUS_FLYING)
        velocity = self.current_flying_velocity
        if flap:  # A new flap
            self.flying_time = 0
            velocity = self.flying_velocity
        velocity = self.inc_speed(velocity, self.flying_velocity,
                                  self.flying_acceleration)
        self.move(time * velocity)
        self.flying_time = self.flying_time + time
        self.current_flying_velocity = velocity

    def _action_fall(self, time):
        self._set_status(self.STATUS_FALLING)
        velocity = self.current_falling_velocity
        velocity = self.inc_speed(velocity, self.falling_velocity,
                                  self.falling_acceleration)
        self.move(-time * velocity)
        self.current_falling_velocity = velocity

    def update(self, time, flap=False):
        if self.got_hit:
            self._action_fall(time)
        else:
            if flap or (self.status == self.STATUS_FLYING and \
                        self.flying_time < BIRD_FLYING_TIME):
                self._action_fly(time, flap)
            else:  # Falling down
                self._action_fall(time)

        # detect collision
        if not self.got_hit:
            hit_tube = collision_detector.bird_hit_tube()
            if hit_tube:
                self._set_status(self.STATUS_HIT_TUBE)
                self.got_hit = True
                # TODO: needs to re-correct bird position to
                # avoid overlap on tube?

        if collision_detector.bird_hit_ground():
            self._set_status(self.STATUS_HIT_GROUND)
            self.got_hit = True
            # NOTE: re-correct bird pos to avoid overlap on ground
            self._set_pos_on_ground()


class CollisionDetector(object):
    def find_bird_nearest_tube(self):
        """Find the nearest tube from the bird"""
        bird_x, bird_y = bird.pos
        for tube in tube_mgr.tubes:
            tube_x, tube_y = tube.pos
            lower_size = tube.lower_size
            if bird_x < tube_x + lower_size[0]:
                return tube
        return None

    def bird_hit_tube(self):
        """Return the tube the bird hit or False otherwise"""
        bird_x, bird_y = bird.pos
        bird_w, bird_h = bird.size
        tube = self.find_bird_nearest_tube()
        if not tube:
            return False
        tube_x, tube_y = tube.pos
        lower_w, lower_h = tube.lower_size

        gap_y1 = tube_y + lower_h
        gap_y2 = gap_y1 + tube.vertical_gap

        # Bird hit lower tube
        if bird_x + bird_w/2 >= tube_x and bird_y - bird_h/2 <= gap_y1:
            log('Bird hit lower tube')
            return tube

        # Bird hit upper tube
        if bird_x + bird_w / 2 >= tube_x and bird_y + bird_h / 2 >= gap_y2:
            log('Bird hit upper tube')
            return tube

        return False

    def bird_hit_ground(self):
        """Return True is the bird hit the ground"""
        bird_x, bird_y = bird.pos
        bird_w, bird_h = bird.size
        grd_x, grd_y = ground.pos
        grd_w, grd_h = ground.size
        return (bird_y - bird_w/2) <= (grd_y + grd_h)

    def bird_out_of_space(self):
        """Return True is the bird flies out of the space"""
        bird_x, bird_y = bird.pos
        bird_size = bird.size
        return (bird_y - bird_size/2) > CANVAS_HEIGHT


class MainView(object):
    def __init__(self):
        self.display = self.create_display()

        global bird, tube_mgr, ground, collision_detector
        bird = Bird()
        ground = Ground()
        tube_mgr = TubeMgr()
        collision_detector = CollisionDetector()

        self.running = False
        self.waiting_to_run = False
        self.waiting_to_restart = False
        self.last_time = None
        self.stop_time = None

        self.score = 0
        self.highest_score = 0
        
        self.score_label = label(pos=(CANVAS_WIDTH/2, CANVAS_HEIGHT*0.8),
                                 height=40, box=True, color=color.white,
                                 text='0')
        self.info_label = label(pos=(100, CANVAS_HEIGHT*0.9),
                                height=20, box=False, color=color.white,
                                text='')

    def create_display(self, title=WINDOW_TITLE,
                       width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                       ll_pos=(0, 0), visible_bounds=False):
        """Create a display window for rendering objects."""
        d = display(title=title, x=100, y=100,
                    width=width, height=height+WINDOW_TITLE_BAR,
                    background=CANVAS_COLOR)
        d.select()
        d.autocenter = False
        d.center = vector(ll_pos) + vector(width, height) / 2.0
        d.autoscale = True
        d.bounds = frame()
        ll_pos = vector(ll_pos)
        corners = [ll_pos,
                   ll_pos + vector(0, height),
                   ll_pos + vector(width, height),
                   ll_pos + vector(width, 0),
                   ll_pos]
        c = curve(frame=d.bounds, radius=0, color=color.white, pos=corners)
        d.autoscale = False
        c.visible = visible_bounds
        return d

    def show_info(self, text):
        if text:
            self.info_label.text = text
            self.info_label.visible = True
        else:
            self.info_label.visible = False

    def set_score(self, score):
        if self.score != score:
            self.score = score
            self.score_label.text = '%d' % score
            # Update highest score
            if self.score > self.highest_score:
                self.highest_score = self.score

    def update(self, time):
        """This function is called each frame to update the render"""
        if not bird.got_hit:
            tube_mgr.update(time)
        bird.update(time, flap=self.mouse_clicked())

        if bird.status == Bird.STATUS_HIT_GROUND:
            self.stop(restart=True)

        # Calculate the score
        last_tube = collision_detector.find_bird_nearest_tube()
        score = last_tube.index if last_tube else 0
        self.set_score(score)

    def mouse_clicked(self):
        clicked = self.display.mouse.clicked
        if self.last_click != clicked:
            self.last_click = clicked
            return True
        return False

    def run(self):
        if self.running or self.waiting_to_run:
            return
        self.running = False
        self.waiting_to_run = True
        self.waiting_to_restart = False

        self.show_info('Click to begin')
        self.last_time = time.time()
        self.last_click = 0

        while True:
            rate(FPS)
            last_time = time.time()
            dt = last_time - self.last_time
            self.last_time = last_time

            if self.running:
                self.update(time=dt)
            else:
                if self.waiting_to_restart:
                    wait_time = 3
                    curr_wait_time = time.time() - self.stop_time
                    if curr_wait_time >= wait_time:
                        self.reset()
                        self.waiting_to_run = True
                        self.waiting_to_restart = False
                        self.show_info('Click to begin')
                    else:
                        remain_time = wait_time - int(curr_wait_time)
                        self.show_info('Game over (%d)' % remain_time)

                elif self.waiting_to_run:
                    if self.mouse_clicked():
                        self.running = True
                        self.waiting_to_run = False
                        self.show_info('Best score: %d' % self.highest_score)

                else:  # No more run needed
                    break
                        
    def stop(self, restart=False):
        if not self.running:
            return
        self.running = False
        self.stop_time = time.time()
        self.waiting_to_restart = restart

    def reset(self):
        bird.reset()
        tube_mgr.reset()
        self.set_score(0)


def main():
    global main_view
    main_view = MainView()
    main_view.run()


main()
