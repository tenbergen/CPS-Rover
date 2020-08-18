from marvelmind import MarvelmindHedge
from threading import Thread
from time import sleep
from sympy import symbols, Eq, solve, Float, nonlinsolve
import math
import queue
import re

# meter
TRACE_CLEARANCE = 0.2
MIN_DISTANCE = 0.2


class Formation(Thread):

    def __init__(self, front_hedge, rear_hedge, gopigo, mmPort, formation_q, xbee_node):
        Thread.__init__(self)

        self.front_hedge = front_hedge
        self.rear_hedge = rear_hedge
        self.gpg = gopigo
        self.mmPort = mmPort
        self.command_q = formation_q  # incoming commands from client
        self.xbee_node = xbee_node

        self.transform = Transform2()
        self.hedge = MarvelmindHedge(tty=self.mmPort, recieveUltrasoundPositionCallback=self.position_update)
        self.hedge.start()

        self.world_obtained = False
        self.is_master = False
        self.robot_list = list()
        self.current_mode = None

        self.target = None
        self.trace = None
        self.world_dict = {}

    def position_update(self):
        position = self.hedge.position()
        if position[0] == self.front_hedge:
            self.transform.front_pos = position[1:3]
        elif position[0] == self.rear_hedge:
            self.transform.rear_pos = position[1:3]
        else:
            pass

    def handle_commands(self):
        while not self.command_q.empty():
            command = self.command_q.get()
            print("handle_commands: ", command)

            if command == "!MASTER":
                self.is_master = True
            elif command == "!NOT_MASTER":
                self.is_master = False
            elif command == "!SNAKE" or command == "!HORI" or command == "!TRI":
                self.current_mode = command
            else:
                self.robot_list = command
                for temp in self.robot_list:
                    self.world_dict[str(temp[1])] = {'pos': self.transform.front_pos, 'target': self.target,
                                                     'trace': self.trace}
                self.world_obtained = True

    # report self to xbee
    def report_to_world(self):
        message = "UPDATE," + str(self.xbee_node.localMac_int) + "," + str(self.transform.front_pos) + "," + str(
            self.trace) + "," + str(self.target)
        self.xbee_node.bc_q.put(message)

    # update self(d0) and world(d1) to world dict
    def update_world(self):
        self.report_to_world()

        d0 = {str(self.xbee_node.localMac_int): {'pos': str(self.transform.front_pos), 'trace': str(self.trace),
                                                 'target': str(self.target)}}
        self.world_dict.update(d0)
        while not self.xbee_node.formation_q.empty():
            # print("update_world: ", self.xbee_node.formation_q.get())
            temp = re.split(r',(?=[^\]]*(?:\[|$))', self.xbee_node.formation_q.get())
            d1 = {temp[1]: {'pos': temp[2], 'trace': temp[3], 'target': temp[4]}}
            self.world_dict.update(d1)

    def select_target(self):
        temp = self.robot_list
        macL = list()
        for robot in temp:
            macL.append(int(robot[1]))
        macL.sort()
        lenth = len(macL) - 1
        index = macL.index(self.xbee_node.localMac_int)
        if lenth == index:
            self.target = None
        else:
            self.target = macL[index + 1]

    def update_trace(self):
        if self.current_mode is None:
            pass
        elif self.current_mode == "!SNAKE":
            self.apply_snake_formation()
        else:
            print("[update Trace] formation not defined")
            self.trace = None

    def apply_snake_formation(self):
        fx = Float(self.transform.front_pos[0], 3)
        fy = Float(self.transform.front_pos[1], 3)
        rx = Float(self.transform.rear_pos[0], 3)
        ry = Float(self.transform.rear_pos[1], 3)

        # print(fx, fy, rx, ry)

        m = (ry - fy) / (rx - fx)
        b = ry - m * rx
        d = TRACE_CLEARANCE

        print(m, b, d)

        x, y = symbols('x y')
        eq1 = Eq(m * x + b - y, 0)
        eq2 = Eq((x - rx) ** 2 + (y - ry) ** 2 - d ** 2, 0)

        solution = solve((eq1, eq2), (x, y), check=False, minimal=True, simplify=False, quick=True)
        # solution = nonlinsolve([eq1, eq2], [x, y])

        s1 = solution.pop()
        s2 = solution.pop()

        x1 = s1[0].evalf(4)
        y1 = s1[1].evalf(4)
        x2 = s2[0].evalf(4)
        y2 = s2[1].evalf(4)

        d1 = math.sqrt((fx - x1) ** 2 + (fy - y1) ** 2)
        d2 = math.sqrt((fx - x2) ** 2 + (fy - y2) ** 2)

        if d1 > d2:
            self.trace = [x1, y1]
        else:
            self.trace = [x2, y2]

    # def go_to_point(self): # TODO calc distance here

    def get_angle(self):
        try:
            a = self.transform.front_pos
            b = self.transform.rear_pos

            tar_pos = self.world_dict.get(str(self.target))['trace']
            print("string_trace:", tar_pos)

            splited = re.findall(r'\d*\.?\d+', tar_pos)
            print("splited:", splited)

            c = [float(splited[0]), float(splited[1])]

            ang = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
            return ang + 360 if ang < 0 else ang
        except Exception as e:
            print("[GET_ANGLE ERROR ]", e)

    def turn_to_face(self, angle):
        if angle <= 180:
            self.gpg.rotate_right(abs(angle), True)
        else:
            self.gpg.rotate_left(abs(angle), True)

    def run(self):

        while not self.world_obtained:
            self.handle_commands()

        self.select_target()

        while True:
            # TODO prob need a sleep command to slow things down?
            sleep(2)
            print(self.world_dict)

            print("self_front", self.transform.front_pos)
            print("self_rear", self.transform.rear_pos)

            try:
                self.handle_commands()
                self.update_world()
                self.update_trace()
            except Exception as e:
                print(e)

            try:
                print("We are getting angle: turnning: ", self.get_angle())
                # self.turn_to_face(self.get_angle())
            except Exception as e:
                print("turn_face error ", e)

            if self.is_master:

                if self.target is not None:  # user gives point
                    print("master not None")
                    # TODO go to target
                    # TODO set self.target = None
                else:
                    print("master pass")
                    pass  # controller

            else:  # slaves follow

                if self.target is not None:
                    print("slave go to target")
                    # TODO go to target
                else:
                    pass  # no mode set yet

        # Tests:

        # while True:
        #     sleep(3)
        #     print("\n\n")
        #     print(self.transform.rear_pos)
        #     print(self.transform.front_pos)
        #     self.handle_commands()
        #
        #     self.report_to_world()
        #     self.update_world()
        #     print("world_dict: ",self.world_dict)
        #     try:
        #         print("print trace: ",self.world_dict['5526146544013111'])
        #     except:
        #         print("trace_fail")
        #         pass


class Transform2:
    def __init__(self, front_pos=None, rear_pos=None):
        self.front_pos = front_pos
        self.rear_pos = rear_pos
