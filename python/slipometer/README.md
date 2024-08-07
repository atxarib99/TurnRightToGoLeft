# Slipometer

Slipometer helps measure wheel slip in both acceleration and deceleration helping to identify when TC/ABS are kicking in. It can help dial brake bias, diff settings, and identify loss of power from TC.

A simple 4 corner view displays the Slip Ratio % in text as well as a bar filling the window. 
When the red bar grows, the tires have a positive slip ratio which means they are rotating faster than ground speed. 
When the blue decends, the tires have a negative slip ratio, which means they are rotating slower than ground speed.

When the bar fills a box, the electronics should be activated and the box will turn white and flash alongside the electronics triggering.

## Adjustability
You can adjust the size of the app by modifying the `size_mult` variable near the top of the file. This is a simple multipicative modifier to the app size.