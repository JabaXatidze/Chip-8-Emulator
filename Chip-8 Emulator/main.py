from tkinter import *
import random
import logging
logging.getLogger().setLevel(logging.DEBUG)


class Chip8:
    def __init__(self) -> None:
        self.memory = [None] * 4096
        self.display = [] 
        for i in range(32):
            self.display.append([0] * 64)
        self.stack = []
        self.pc = 512
        self.v = [0] * 16
        self.index = 0
        self.key = []
        self.keypad = {"1": 1, "2": 2, "3": 3, "4": 12, "q": 4, "w": 5, "e": 6, "r": 13, "a": 7, "s": 8, "d": 9, "f": 14, "z": 10, "x": 0, "c": 11, "v": 15}
        self.delay_timer = 0
        self.sound_timer = 0
        
    def update_screen(self):
        # for row in range(32):
        #     for column in range(64):
        #         if self.display[row][column] == 1:
        #             my_canvas.canvas.itemconfig(my_canvas.pixels[row][column], fill="black")
        #         else: 
        #             my_canvas.canvas.itemconfig(my_canvas.pixels[row][column], fill="white")
        pass

    
    def load(self, file, index):
        with open(file, "rb") as f:
            i = index
            while True:
                data = f.read(1)
                if not data:
                    break
                self.memory[i] = data
                i+=1


class CanvasWrapper:
    def __init__(self, title) -> None:
        self.pixels = [] 
        for i in range(32):
            self.pixels.append([None] * 64)
        self.window = Tk()
        self.radius = 20
        self.diameter = 2+self.radius
        self.canvas = Canvas(self.window, height=32*self.diameter, width=64*self.diameter)
        def create_circle(column, row):
            x1 = column*self.diameter
            y1 = row*self.diameter
            x2 = x1 + self.diameter  
            y2 = y1 + self.diameter
            return self.canvas.create_oval(x1, y1, x2, y2, fill="white")

        for row in range(32):
            for column in range(64):  
                self.pixels[row][column] = create_circle(column, row)
        
        self.canvas.pack()

         
        
chip = Chip8()
chip.load(".\\Fonts.ch8", 80)
chip.load(".\\IBM Logo.ch8", 512)   
my_canvas = CanvasWrapper("IBM Logo")



def extract_first_nibble(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\xf0\x00", "big")) >> 12

def extract_second_nibble(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\x0f\x00", "big")) >> 8

def extract_third_nibble(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\x00\xf0", "big")) >> 4

def extract_fourth_nibble(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\x00\x0f", "big"))

def extract_NN(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\x00\xff", "big"))

def extract_NNN(instruction):
    return (int.from_bytes(instruction, "big") & int.from_bytes(b"\x0f\xff", "big"))

def key_press(event):
    key = chip.keypad[event.char]
    chip.key = key
    logging.debug(f"Key {chip.key} was pressed")

def game_loop(chip):
    my_canvas.window.bind("<Key>", key_press)
    instruction = chip.memory[chip.pc] + chip.memory[chip.pc+1]
    first_nibble = extract_first_nibble(instruction)
    logging.debug(f"The instruction {bytearray(instruction).hex()}")
    # logging.debug(instruction)
    # print(type(first_nibble))
    chip.pc+=2
    # print(pc)
    # clears screen
    if instruction == b"\x00\xe0":
        logging.debug("Clears screen")
        for row in chip.display:
            for pixel in row:
                pixel = 0
    # sets pc to the last address in the stack
    elif instruction == b"\x00\xee":
        chip.pc = chip.stack.pop()
        logging.debug(f"Retrieves program counter from the stack")
    # jumps to NNN
    elif first_nibble == 1:
        chip.pc = extract_NNN(instruction)
        logging.debug(f"Counter jumps to {chip.pc}")
    # pushes current pc to the stack, then jumps to NNN
    elif first_nibble == 2:
        chip.stack.append(chip.pc)
        chip.pc = extract_NNN(instruction)
        logging.debug(f"Stacks the current pc and jumps to {chip.pc}")
    # skips one instruction 
    elif first_nibble == 3:
        logging.debug(f"If register at {extract_second_nibble(instruction)} (value : {str(chip.v[extract_second_nibble(instruction)])}) equals {str(extract_NN(instruction))}")
        if chip.v[(extract_second_nibble(instruction))] == extract_NN(instruction):
            chip.pc+=2
    # skips one instruction 
    elif first_nibble == 4:
        if chip.v[extract_second_nibble(instruction)] != extract_NN(instruction):
            chip.pc+=2
        logging.debug(f"If value of register {extract_second_nibble(instruction)} ({chip.v[extract_second_nibble(instruction)]}) does not equal {extract_NN(instruction)}, skips an instruction")
    #
    elif first_nibble == 5:
        if chip.v[extract_second_nibble(instruction)] == chip.v[extract_third_nibble(instruction)]:
            chip.pc+=2
        logging.debug(f"If values of registers {extract_second_nibble(instruction)} ({chip.v[extract_second_nibble(instruction)]}) and {extract_third_nibble(instruction)} ({chip.v[extract_third_nibble(instruction)]}) equal each other, skips an instruction")
    
    # sets register VX
    elif first_nibble == 6:
        chip.v[extract_second_nibble(instruction)] = extract_NN(instruction)
        logging.debug(f"Puts {extract_NN(instruction)} in register {extract_second_nibble(instruction)}")
    # adds register VX
    elif first_nibble == 7:
        chip.v[extract_second_nibble(instruction)] += extract_NN(instruction)
        logging.debug(f"Adds {extract_NN(instruction)} to {extract_second_nibble(instruction)} in register {chip.v[(extract_second_nibble(instruction))]}")
    #
    elif first_nibble == 8:
        x = extract_second_nibble(instruction)
        y = extract_third_nibble(instruction)
        n = extract_fourth_nibble(instruction)
        if n == 0:
            chip.v[x] = chip.v[y]
        elif n == 1:
            chip.v[x] = chip.v[x] | chip.v[y] 
        elif n == 2:
            chip.v[x] = chip.v[x] & chip.v[y]
        elif n == 3:
            chip.v[x] = chip.v[x] ^ chip.v[y]
        elif n == 4:
            chip.v[x] += chip.v[y]
            if chip.v[x] > 255:
                chip.v[15] = 1
            else:
                chip.v[15] = 0
        elif n == 5:
            if chip.v[y] > chip.v[x]:
                chip.v[15] = 1
            else:
                chip.v[15] = 0
            chip.v[x] = chip.v[y] - chip.v[x]
            logging.debug(f"Compares register {x} and register {y} and assigns boolean value to register 15. Subtracts register {x} from register {y} and puts the value in register {x}")
        elif n == 7:
            if chip.v[x] > chip.v[y]:
                chip.v[15] = 1
            else:
                chip.v[15] = 0
            chip.v[x] = chip.v[x] - chip.v[y]
            logging.debug(f"Compares register {x} and register {y} and assigns boolean value to register 15. Subtracts register {y} from register {x} and puts the value in register {x}")
        elif n == 6:
            chip[15] = chip.v[y] & int.from_bytes(b"\x00\x01", "big")
            chip.v[x] = chip.v[y] >> 1
        elif n == 14:
            if chip.v[y]>2**7:
                chip[15] = 1
            else:
                chip[15] = 0
            chip.v[x] = chip.v[y] << 1            
    #
    elif first_nibble == 9:
        if chip.v[(extract_second_nibble(instruction))] != chip.v[(extract_third_nibble(instruction))]:
            chip.pc+=2
        logging.debug(f"If values of registers {extract_second_nibble(instruction)} ({chip.v[extract_second_nibble(instruction)]}) and {extract_third_nibble(instruction)} ({chip.v[extract_third_nibble(instruction)]}) do not equal each other, skips an instruction")
    # sets index register I
    elif first_nibble == 10:
        chip.index = extract_NNN(instruction)
        logging.debug(f"Assigns {chip.index} to index register")
    elif first_nibble == 11:
        chip.pc = chip.index+(extract_NNN(instruction))
        logging.debug(f"Sets program counter to {chip.pc}")
    elif first_nibble == 12:
        rand = random.randrange(0,255)
        chip.v[extract_second_nibble(instruction)] = rand & (extract_NN(instruction))
        logging.debug(f"Puts a random number in register {chip.v[extract_second_nibble(instruction)]}")
    # displays sprite
    elif first_nibble == 13:
        chip.v[15] = 0
        vx = chip.v[(extract_second_nibble(instruction))] & 63
        vy = chip.v[(extract_third_nibble(instruction))] & 31
        sprite = chip.memory[chip.index:chip.index+(extract_fourth_nibble(instruction))]
        logging.debug(f"Draws sprite at coordinates {vx}, {vy}")
        for j, b in enumerate(sprite):
            logging.debug(bin(int.from_bytes(b, "big")).strip('0b'))
            for i in range(8):
                if vx+i < len(chip.display[0]) and vy+j < len(chip.display):
                    if int.from_bytes(b, "big") & 2**(7 -i) & chip.display[vy+j][vx+i]:
                        chip.v[15] = 1
                    val = 1 if int.from_bytes(b, "big") & 2**(7 -i) > 0 else 0
                    chip.display[vy+j][vx+i] = val ^ chip.display[vy+j][vx+i]
                    if chip.display[vy+j][vx+i] == 1:
                        my_canvas.canvas.itemconfig(my_canvas.pixels[vy+j][vx+i], fill="black")
                    else: 
                        my_canvas.canvas.itemconfig(my_canvas.pixels[vy+j][vx+i], fill="white")
        # chip.update_screen(vx, vy)
    elif first_nibble == 14:
        if (extract_NN(instruction)) == 158:
            if chip.v[extract_second_nibble(instruction)] == chip.key:
                chip.pc += 2
            logging.debug(f"If {chip.v[extract_second_nibble(instruction)]} at register {extract_second_nibble(instruction)} is equal to {chip.key}, skips an instruction")
        elif (extract_NN(instruction)) == 161:  
            if chip.v[extract_second_nibble(instruction)] != chip.key:
                chip.pc += 2 
            logging.debug(f"If {chip.v[extract_second_nibble(instruction)]} at register {extract_second_nibble(instruction)} is not equal to {chip.key}, skips an instruction")
    elif first_nibble == 15:
        nn = extract_NN(instruction)
        x = extract_second_nibble(instruction)
        if nn == 7:
            chip.v[x] = chip.delay_timer
        elif nn == 10:
            if chip.key:
                chip.v[x] = chip.key
            else:
                chip.pc-=2

        elif nn == 21:    
            chip.delay_timer = chip.v[x]
        elif nn == 24:
            chip.sound_timer = chip.v[x]
        elif nn == 30:
            chip.index+=chip.v[x]
        elif nn == 33:
            chip.memory[chip.index] = chip.v[x] // 100
            chip.memory[chip.index+1] = (chip.v[x] // 10) % 10
            chip.memory[chip.index+2] = chip.v[x] % 10
        elif nn == 41:
            chip.index = ((chip.v[x]%16) * 5) + 80
            logging.debug(f"Index set to {((chip.v[x] % 16) * 5) + 80}")
        elif nn == 85:
            for i in range(chip.v[x]):
                chip.memory[chip.index+i] = chip.v[i]
        elif nn == 101:
            for i in range(chip.v[x]):
                chip.v[i] = chip.memory[chip.index+i]




    else:    
        raise Exception("")
    logging.debug(f"PC - {chip.pc}, Index - {chip.index}, Registers - {str(chip.v)}")
    if chip.delay_timer:
        chip.delay_timer -= 1
    my_canvas.window.after(1, game_loop, chip)


my_canvas.window.after(1, game_loop, chip)
my_canvas.window.mainloop()


    

