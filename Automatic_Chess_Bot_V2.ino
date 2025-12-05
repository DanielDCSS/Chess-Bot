#include <VarSpeedServo.h>

//Decalring the servos:
VarSpeedServo servo1; //Rotation
VarSpeedServo servo2; //Arm
VarSpeedServo servo3; //Forearm
VarSpeedServo servo4; //Claw

//Declaring the speed:
int speed = 15;
int Delay = 1000;
float M = 0.5;

//Declaring the pin:
int pin1 = 2;


//Declaring the button:
int RobotTurnButton;


int Offsets[3] = {1, 1, 0};


//Declaring the coordinate arrays:
int Rotation[65] = {
    64, 70, 78, 87, 96, 105, 113, 122,
    65, 71, 79, 87, 95, 103, 111, 119,
    67, 74, 80, 87, 93, 102, 109, 115,
    70, 75, 80, 87, 94, 100, 107, 113,
    70, 75, 81, 86, 93, 98, 104, 110,
    71, 76, 81, 87, 92, 98, 103, 108,
    72, 77, 82, 87, 92, 97, 102, 106,
    72, 76, 81, 86, 91, 96, 100, 104,
    170
};
int Arm_Down[65] = {
    52, 50, 47, 45, 44, 47, 48, 50,
    60, 58, 57, 55, 55, 55, 55, 57,
    65, 62, 60, 61, 61, 61, 62, 63,
    74, 71, 69, 69, 68, 68, 71, 71,
    81, 78, 77, 76, 77, 77, 78, 80,
    89, 88, 85, 84, 84, 85, 87, 89,
    101, 96, 94, 94, 95, 94, 98, 99,
    117, 116, 111, 108, 108, 108, 111, 117,
    20
};
int Forearm_Down[65] = {
    58, 55, 57, 56, 56, 55, 59, 59,
    60, 59, 57, 55, 56, 58, 60, 64,
    68, 67, 66, 65, 65, 66, 69, 69,
    72, 74, 73, 72, 72, 72, 70, 73,
    80, 80, 79, 79, 76, 76, 76, 79,
    89, 87, 84, 84, 84, 84, 85, 87,
    97, 93, 92, 92, 92, 92, 96, 96,
    117, 114, 107, 104, 104, 104, 109, 117,
    120
};
int Arm_Up[65] = {
    24, 18, 18, 20, 16, 19, 20, 20,
    35, 32, 31, 30, 30, 31, 32, 32,
    43, 42, 41, 39, 39, 39, 41, 40,
    54, 49, 49, 48, 48, 45, 51, 45,
    63, 57, 56, 55, 53, 56, 57, 60,
    72, 73, 72, 72, 72, 72, 72, 73,
    90, 80, 80, 80, 80, 80, 80, 87,
    100, 99, 94, 91, 91, 91, 94, 100,
    20
};
int Forearm_Up[65] = {
    121, 122, 117, 117, 117, 117, 121, 122,
    107, 106, 102, 101, 101, 102, 105, 110,
    106, 98, 100, 103, 103, 103, 105, 120,
    115, 115, 115, 115, 115, 115, 115, 115,
    115, 115, 115, 115, 115, 115, 115, 115,
    116, 116, 113, 113, 113, 113, 114, 116,
    126, 122, 121, 121, 121, 121, 125, 125,
    147, 144, 137, 134, 134, 134, 139, 147,
    120
};

//Declaring the claw positions:
  int Claw_Open = 82;
  int Claw_Closed = 128;


//Declaring the move array:
int Movement[5]; //{origin square, destination square, capture (boolean), capture square, castle (0 or 1 or 2)}




void Move(int Origin, int Destination)
{

delay(50);

servo1.slowmove (Rotation[Origin]+Offsets[0], speed);
servo2.slowmove (Arm_Up[Origin]+Offsets[1], speed);
servo3.slowmove (Forearm_Up[Origin]+Offsets[2], speed);

servo4.slowmove (Claw_Open, speed);

delay(4*Delay);


servo2.slowmove (Arm_Down[Origin]+Offsets[1], M*abs(Arm_Down[Origin]-Arm_Up[Origin]));
servo3.slowmove (Forearm_Down[Origin]+Offsets[2], M*abs(Forearm_Up[Origin]-Forearm_Down[Origin]));

delay(Delay);

servo4.slowmove (Claw_Closed, speed);

delay(Delay+500);

servo2.slowmove (Arm_Up[Origin]+Offsets[1], speed);
servo3.slowmove (Forearm_Up[Origin]+Offsets[2], speed+5);

delay(Delay);

servo1.slowmove (Rotation[Destination]+Offsets[0]+10, speed);
servo2.slowmove (Arm_Up[Destination]+Offsets[1], speed);
servo3.slowmove (Forearm_Up[Destination]+Offsets[2], speed);

delay(2*Delay);

servo1.slowmove (Rotation[Destination]+Offsets[0], speed);

delay(Delay);

servo2.slowmove (Arm_Down[Destination]+Offsets[1], M*abs(Arm_Down[Destination]-Arm_Up[Destination]));
servo3.slowmove (Forearm_Down[Destination]+Offsets[2], M*abs(Forearm_Up[Destination]-Forearm_Down[Destination])+5);

delay(Delay);

servo4.slowmove (Claw_Open, speed);

delay(Delay);

servo2.slowmove (Arm_Up[Destination]+Offsets[1], speed);
servo3.slowmove (Forearm_Up[Destination]+Offsets[2], speed+5);

delay(Delay);

servo1.slowmove (170+Offsets[0], speed);
servo2.slowmove (20+Offsets[1], speed);
servo3.slowmove (120+Offsets[2], speed);

delay(1000);

}




void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  
  pinMode(pin1, INPUT_PULLUP);

   
  //Attaching the servos to pins:
  servo1.attach(6);
  servo2.attach(9);
  servo3.attach(10);
  servo4.attach(11);
}

void loop() {
  // put your main code here, to run repeatedly:
  
  //Assigning the button to pin:
  RobotTurnButton = digitalRead(pin1);
  
 
  //Instructions for if the robot needs to move ball from position 1 to 2:
  if(RobotTurnButton == LOW) {
    if (Movement[4] == 1){
      Move(0, 3);
      Move(4, 2);

    }
    else if (Movement[4] == 2){
      Move(7, 5);
      Move(4, 6);

    }
    else if (Movement[2] == true){
      Move(Movement[3], 64);
      Move(Movement[0], Movement[1]);

    }
    else {
      Move(Movement[0], Movement[1]);

    }
  }
}