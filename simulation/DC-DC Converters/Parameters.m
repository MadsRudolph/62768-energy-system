d=0.5;
R=7;
L=820e-6;
f=5000;
C=2200e-6;
Vin=14;
k=[0.1:0.1:0.9]
Va=Vin.*k
Ia=Va/R
dI=Vin*k.*(1-k)/(f*L)
dVc=Vin*k.*(1-k)/(8*f*L*C*f)



% Buck
k=[0.1:0.1:0.9]
Vo=k*Vin
dImax=Vin*k.*(1-k)/(f*L)
dVcmax=Vin*k.*(1-k)/(8*f*L*C*f)


% Boost

R=50;
Vin=5;
T=1/f;
z=T*R/L;
Va=Vin./(1-k)
Ia=Va/R

dImax=Vin*k/(f*L)
dVcmax=Ia.*k/(f*C)


% Buck boost
Va=Vin.*k./(1-k)
Ia=Va/R
k
dImax=Vin*k/(f*L)
dVcmax=Ia.*k/(f*C)