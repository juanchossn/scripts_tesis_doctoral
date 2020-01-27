%%%%%%%%%%%%%% Diagnostico general: simulaciones a rhoW=0 %%%%%%%%%%%%%%%%%
clear
plotFlag  = true;
closeFlag = true;
%% Levanto datos a rhoW = 0
simDataRoot = 'SOSSEP2019';
simData = [simDataRoot '_00'];
load(simData)
rho = rho'; % Traspongo datos para que quede en formato entry-field
%% Genero struc con los valores de las variables
numVar = length(varlab);

% vari: matriz con los parametros de entrada

for v = 1:numVar
    variVal.(varlab{v}) = unique(vari(:,v));
end
variVal.zenith_sol
variVal.zenith_obs

%% Firmas a TOA (sin RC): ploteo
if plotFlag
    plot(lambdas,rho(:,1:100))
    ylabel('\rho^{TOA}[\rho_{w}=0]')
    xlabel('Wavelength [nm]')
    Figuras.sizes(20,20,2,1)
    set(gca,'yscale','log')
	Figuras.saveMaximized(closeFlag,'./figures/SOS_TOA')
end
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%% SUNGLINT (SG) %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% SG: Definitions

SG.tau     = 0;     % Sin aerosoles
SG.lambda  = 2320;  % Se asume Rayleigh[2320nm] ~ 0
SG.thresh  = 0.005; % cf. Mobley et al. 2016 ("Atmospheric Correction Tutorial"), pp. 42
SG.noAer   = vari(:,strcmp(varlab,'tau_aer'))==SG.tau;       % Selecciono datos sin aerosoles
SG.noAerM1 = SG.noAer & vari(:,strcmp(varlab,'mod_aer'))==1; % Como hay 15 modelos de aerosoles, me quedo con WMO = 1 (para que no se repitan)
SG.rho     = rho(lambdas==SG.lambda,SG.noAerM1)'; % Reflectancia por sunglint
% Computo La distancia euclidea en el espacio (tita,phi)~R2: |(\theta_{v}-\theta_{s},\Delta\phi)||_{2}
SG.angle   = sqrt(vari(SG.noAerM1,strcmp(varlab,'phi_obs')).^2 + ...
    (vari(SG.noAerM1,strcmp(varlab,'zenith_sol')) - vari(SG.noAerM1,strcmp(varlab,'zenith_obs'))).^2);
%% SG: El phi reciproco es 0 o 180?
% Testeo con phi = 0 y phi = 180 (angulo azimutal relativo), para ver cual
% es el especular respecto de la superficie del agua.

% RTA = 0: El rhoSG se maximiza para "SG.angle" bajo, lo cual es RARO
% (chequear definicion en el Manual de SOS!)

phiTest =   [0 180];

if plotFlag
    for sp=1:length(phiTest)
        subplot(length(phiTest),1,sp)
        hold on
            plot(  SG.rho(vari(SG.noAerM1,7)==phiTest(sp)),'k'  ) % rho_SG para todos los escaneos con phi = 0 | phi = 180
            plot(SG.angle(vari(SG.noAerM1,7)==phiTest(sp)),'--k') % Distancia euclidea entre los angulos solar y de observacion.
        hold off

        set(gca,'YScale','log')
        xlim([0 60     ])
        ylim([0.0001 1000])
        set(gca,'YTick',logspace(-4,3,8))
        if sp == length(phiTest)
            hleg = legend('Sunglint reflectance, \rho_{SG}','Angular distance to sunglint, ||(\theta_{v}-\theta_{s},\Delta\phi)||_{2}');
            set(hleg,'Location','best')
            xlabel('Scenario nr.')
        end
        ylabel(['Reflectance/' newline 'Angular distance'])
        title(['\Delta\phi = ' num2str(phiTest(sp))])
        Figuras.sizes(20,20,2,1)
    end
    
    Figuras.saveMaximized(closeFlag,'./figures/SG_ReciprocalRAA')
end

%% SG: histograma
% Histograma de reflectancias por sunglint.
if plotFlag
    % Histograma rhoSg
    close
    % hold on
    [freq,xbin] = hist(SG.rho,10000);
    bar(xbin,freq)
    set(gca,'XScale','log')
    ylabel('Occurrences')
    xlabel('Sunglint reflectance, \rho_{SG}')
    xlim([0.001 20])
    ylim([0 1.1*max(freq)])
    hold on;
    plot(SG.thresh*[1 1], ylim, 'LineWidth', 0.5, 'Color', 'r');
    text(SG.thresh,0.9*max(freq),['SG threshold: ' num2str(SG.thresh)],'color','r')
    Figuras.sizes(20,30,2,1)
	Figuras.saveMaximized(closeFlag,'./figures/SG_Histogram')
end
%% SG: Distribucion angular de la reflectancia por reflexion especular

%%% SG: plot polar
% SG.rho vs. SG.angle

% SG.noAerM1: subconjunto de parametros sin aerosoles.

SG.titaObs = vari(SG.noAerM1,strcmp(varlab,'zenith_obs'));
SG.phiRel  = vari(SG.noAerM1,strcmp(varlab,'phi_obs'   ));

% Asigno coordenadas polares a cada par (tita,phi):
% 1) El angulo cenital de observacion (tita) se toma como el "radio"
% 2) El angulo azimutal relativo (phi) se toma como el "angulo polar"
SG.polarCoord = SG.titaObs.*[-cosd(SG.phiRel) sind(SG.phiRel)];

% Haremos dos plots polares, segun valor (booleano) de condPlot0
condPlot0 = [true false];
% condPlot0 = false: sunglint_reflectance;
% condPlot0 = true : flag based on sunglint_reflectance>SG.thresh;

if plotFlag
    for cp = 1:length(condPlot0)
        condPlot = condPlot0(cp);
        if condPlot
            colNum = 2;
            cPlotStr = 'Thresh';
        else
            colNum = 256;
            cPlotStr = '';
        end
        figure; sp = 0;
        % Cada subplot correspondera a un valor de viento y un valor de SZA
        % (Solar Zenith Angle)
        for ts = 1:length(variVal.zenith_sol)
            titaSol = variVal.zenith_sol(ts);
            for w = 1:length(variVal.w)
                sp = sp + 1;
                wind    = variVal.w(w);

                % dentro del subconjunto SG.noAerM1 (sin aerosoles) me
                % quedo con los de viento y SZA especificos.
                condSolZenWind = vari(SG.noAerM1,strcmp(varlab,'zenith_sol')) == titaSol & ...
                                 vari(SG.noAerM1,strcmp(varlab,'w'))          == wind;

                % Defino los colores del scatterplot a partir de las 
                % relfectancias por sunglint para la escala de colores
                % considerada.
                colVec = SG.rho(condSolZenWind);
                if condPlot
                    colVec = colVec>=SG.thresh;
                end


                subplot(length(variVal.zenith_sol),length(variVal.w),sp)
                scatter(SG.polarCoord(condSolZenWind,1),SG.polarCoord(condSolZenWind,2),60,colVec,'filled')
                Figuras.sizes(12,20,2,1)
                Figuras.colMap(viridis(colNum))
                ylim([0   70])
                xlim([-70 70])
                daspect([1 1 1])

                if ts == 1
                     title(['viento = '          num2str(round(wind*100)/100)    ' m/s'])
                end
                if w  == 1
                    ylabel(['\theta_{s} = ' num2str(round(titaSol*100)/100) 'º'])
                end
                if ts == length(variVal.zenith_sol) && w  == length(variVal.w)
                    clbr = Figuras.colbar('\rho_{g}');
                    if condPlot
                        set(clbr,'YTick',[0 1]);
                        set(clbr,'YTickLabel',{'\leq 0.005';'>0.005'});
                    end
                end

            end
        end
        mtit('Reflectancia del sunglint vs. (\theta_{v},\phi) [Polar]','FontSize',16)
        Figuras.saveMaximized(closeFlag,['./figures/SG_ObservingGeometry' cPlotStr])
    end
end
%% SG: conditional flag based on SG.thresh
% SG.glinted es la flag por sunglint elevado aplicable al conjunto entero 
% de simulaciones

SG.glinted = false(0);
for mod_aer = 1:length(variVal.mod_aer)
    for tau_aer = 1:length(variVal.tau_aer)
        % concateno vector booleano para cada condicion aerosolar
        SG.glinted = [SG.glinted; SG.rho>=SG.thresh];
	end
end

%% SG: grafico espectros con/sin suglint
if plotFlag
    M = 1500; % grafico los primeros M espectros
    firstMspectra = [true(M,1); false(size(rho,2) - M,1)];
    hold on
        sg  = plot(lambdas,rho(:,firstMspectra &  SG.glinted),'y');
        nsg = plot(lambdas,rho(:,firstMspectra & ~SG.glinted),'b');
    hold off
    legend([nsg(1) sg(1)], ['\rho_{SG} < ' num2str(SG.thresh)],['\rho_{SG} \geq ' num2str(SG.thresh)])
    xlabel('Wavelength[nm]')
    ylabel('TOA total reflectance for black water, \rho_{t}^{TOA}[\rho_{w}=0]')
    Figuras.sizes(16,16,2,1)
    set(gca,'YScale','log')
	Figuras.saveMaximized(closeFlag,['./figures/RC_SGCondition'])
end
%%
%%%%%%%%%%%%%%%%%%%%%%%% RAYLEIGH CORRECTION (RC) %%%%%%%%%%%%%%%%%%%%%%%%%
%% RC: Perform Rayleigh correction for each aerosol condition

RC.rho     = zeros(size(rho));
RC.noAer   = SG.noAer;
for tau_aer = 1:length(variVal.tau_aer)
    condAer = vari(:,strcmp(varlab,'tau_aer')) == variVal.tau_aer(tau_aer);
    RC.rho(:,condAer) = rho(:,condAer) - rho(:,RC.noAer);
    % NB: "SG.noAer" incluye repeticiones dados los 15 modelos de la WMO
    % La resta rho(:,condAer) - rho(:,RC.noAer) es a tauAER!=0 vs tauAER=0
end
RC.wmoPure = max(atmos(vari(:,3),:),[],2)==1; % Para eventualmente plotear sólo escenarios puros
%% RC: Plot rhoRC y rhoTOT for different aerosol Taus and Models
if plotFlag
    sp = 0;
    wmoPure = [1 5 15];
    taus    = [0.1 0.2 0.3];
    for tau_aer = taus
        for mod_aer = wmoPure
            condAer = round(10*vari(:,strcmp(varlab,'tau_aer'   )))/10 == tau_aer & ...
                               vari(:,strcmp(varlab,'mod_aer'   ))     == mod_aer & ...
                               vari(:,strcmp(varlab,'zenith_sol'))     == 28.7684 & ...
                               vari(:,strcmp(varlab,'zenith_obs'))     == 28.7700 & ...
                               vari(:,strcmp(varlab,'phi_obs'   ))     == 180;
            sp = sp + 1;
            subplot(length(taus),length(wmoPure),sp)
                hold on
                    h = plot(lambdas,   rho(:,condAer & ~SG.glinted), '-r');
                    g = plot(lambdas,RC.rho(:,condAer & ~SG.glinted), '-g');
                hold off
                ylim([-0.01 0.25])
                if     tau_aer == taus(1)
                    text(0.2,0.9,['WMO: ' wmoLegends{mod_aer}],'Units','normalized')
                elseif tau_aer == taus(end)
                    xlabel('Longitud de onda [nm]')
                end
                if     mod_aer == 1
                    ylabel(['Reflectancia' newline '(\tau_{a}(500) = ' num2str(tau_aer) ')'])
                end
                if     tau_aer == taus(end) && mod_aer == wmoPure(end)
                    legend([h(1) g(1)],'\rho_{TOA}','\rho_{RC}')
                end
                Figuras.sizes(16,16,2,1)
        end
    end
    mtit('\theta_{s}=\theta_{v}=30º y \phi=180º')
    Figuras.sizes(16,16,2,1)
	Figuras.saveMaximized(closeFlag,['./figures/RCvsTOA_OAA_30_OZA_30_RAA_180'])
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%% MULTISPECTRAL SENSORS (SENS) %%%%%%%%%%%%%%%%

%% SENS: Convolute with SRFs
% Convolouciona la rhoRC con las SRFs
sensors = {'MA'; 'MT'; 'VIIRS'; 'MSI'; 'SMAR'};
% sensors = {'SMAR'};
for s = 1:length(sensors)
    sensor = sensors{s};
    sensMatFile = [simData '_' sensor '.mat'];
    if exist(sensMatFile)==0
        [waveBandMean,rhoBand] = hyp2satBands(lambdas,RC.rho,sensor);
        save(sensMatFile,'waveBandMean','rhoBand')
    else
        load(sensMatFile)
    end
    SENS.(sensor).rhoRC = rhoBand;
	SENS.(sensor).bands = round(waveBandMean);
end
spare = 0;
%% SENS: Select PCA bands for each sensor (Display list)
clc
for s = 1:length(sensors)
    sensor = sensors{s};
    bands = SENS.(sensor).bands;
    if plotFlag
        disp([sensor ' SWIR ' num2str(bands(bands>900))])
        disp([sensor ' REST ' num2str(bands(bands<900))])
    end
    % Originalmente, la idea era corregir las bandas NIR nomas, luego
    % se agregaron las restantes, pero quedo el nombre NIR... 
    SENS.(sensor).bandsPcaNir = bands(bands<900);
end

%% SENS: Select PCA bands for each sensor (Fix list)
SENS.MA   .bandsPcaBlack = [1241 1628 2114];
SENS.MT   .bandsPcaBlack = [1241 1628 2114];
SENS.VIIRS.bandsPcaBlack = [1241 1602 2257];
SENS.MSI  .bandsPcaBlack = [     1614 2202];
SENS.SMAR .bandsPcaBlack = [1240      1640];

% Merge pcaBlack and pcaNir bands

for s = 1:length(sensors)
    sensor = sensors{s};
    SENS.(sensor).bandsPca = [SENS.(sensor).bandsPcaNir SENS.(sensor).bandsPcaBlack];
end

% Indices de bandas
for s = 1:length(sensors)
    sensor = sensors{s};

    [~,idx,~] = intersect(SENS.(sensor).bands,SENS.(sensor).bandsPcaBlack);
    SENS.(sensor).bandsPcaBlackIdx = idx;

	[~,idx,~] = intersect(SENS.(sensor).bands,SENS.(sensor).bandsPcaNir  );
    SENS.(sensor).bandsPcaNirIdx   = idx;
    
    [~,idx,~] = intersect(SENS.(sensor).bands,SENS.(sensor).bandsPca     );
    SENS.(sensor).bandsPcaIdx = idx;
end

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%% PCA %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% PCA: Scatter plots rhoRC(bandas a corregir) vs. rhoRC(bandas SWIR)

PCA.cond = ~SG.glinted & ~RC.noAer;
if plotFlag
    pure = false;
    % pure: solo se plotean escenarios "puros" C, M y U

    graphCond = PCA.cond;
    if pure
        graphCond = graphCond & RC.wmoPure;
    end

    colMap = jet(length(variVal.mod_aer)); % coloreados segun aerosoles
    for s = 1:length(sensors)
        sensor = sensors{s};
        bandsNir     = SENS.(sensor).bandsPcaNir; 
        nBandsNir    = length(bandsNir);
        for b = 1:nBandsNir
            figure
            % los scatters van a ser rhoRC de una banda "bandsNir(b)" a ser
            % corregida vs. todas las bandas SWIR.
            bands  = [bandsNir(b) SENS.(sensor).bandsPcaBlack];
            % get band indices
            [~,bandsIdx,~] = intersect(SENS.(sensor).bands,bands);
            nBands = length(bands);
            sp = 0;
            for by = 1:nBands
                by0  = bandsIdx(by);
                rhoy = SENS.(sensor).rhoRC(PCA.cond,by0);
                for bx = 2:nBands
                    bx0  = bandsIdx(bx);
                    rhox = SENS.(sensor).rhoRC(PCA.cond,bx0);
                    sp = sp + 1;
                    if bx>by
                        subplot(nBands-1,nBands-1,sp)
                        hold on
                        % Fit linear
                        lin0  =  polyfit(rhox,rhoy,1);
                        slop0 = lin0(1);
                        bias0 = lin0(2);
                        corr0 = corrcoef(rhox,rhoy);
                        corr0 = corr0(1,2);

                        scatter(rhox,rhoy,15,atmos(vari(PCA.cond,strcmp(varlab,'mod_aer')),:),'filled')
                        plot([-0.1 0.3],slop0*[-0.1 0.3]+bias0,'k')
                        plot([-0.1 0.3],[-0.1 0.3],'--k')
                        axis([-0.1 0.3 -0.1 0.3])
                        daspect([1 1 1])
                        pos = get(gca,'Position');
                        pos(3) = pos(3)*1.3;
                        pos(4) = pos(4)*1.3;
                        pos(1) = pos(1) - 0.5*pos(3)*(bx-2);
                        pos(2) = pos(2) - 0.1*pos(3);
                        set(gca,'Position',pos);

                        text(0.5,0.18,['m = ' sprintf('%0.4f',slop0)],'units','normalized')
                        text(0.5,0.12,['b = ' sprintf('%0.4f',bias0)],'units','normalized')
                        text(0.5,0.06,['r = ' sprintf('%0.4f',corr0)],'units','normalized')


                        if bx-by~=1
                            set(gca,'XTickLabel','')
                            set(gca,'YTickLabel','')
                        else
                            ylabel(['\rho_{RC}[' num2str(bands(by)) ']']);
        %                     posY = get(ylabh,'Position');
        %                     set(ylabh,'Position',posY + [0 0 1])
                        end
                        if by == 1
                            title (['\rho_{RC}[' num2str(bands(bx)) ']'])
                        end
                        if by == nBands
        %                     set(gca,'YAxisLocation','right')
                        end
                        if bx == nBands && by == nBands-1
                            Figuras.colMap([1 0 0; 0 1 0; 0 0 1])
                            clbr = Figuras.colbar('Escenarios WMO');
                            set(clbr,'YTick',[1 3 5]/6)                            
                            set(clbr,'YTickLabel',{'C';'M';'U'})
                            text(-nBands + 2,0.5,['Sensor: ' sensor],'units','normalized')
                        end
                        Figuras.sizes(16,12,2,1)
                        hold off
                    end
                end
            end
            figname = ['./figures/rhoRCAllvsAll_' sensor '_' num2str(bandsNir(b))];
            Figuras.saveMaximized(closeFlag,figname)
        end
    end
end
%% Videos with scatter plots
if plotFlag
    for s = 1:length(sensors)
        disp(['Creating video for: ' sensors{s}])
        sensor = sensors{s};
        bandsNir     = SENS.(sensor).bandsPcaNir;
        nBandsNir    = length(bandsNir);
        writerObj = VideoWriter(['./figures/rhoRCAllvsAll_' sensor '.avi']);
        writerObj.FrameRate = 2;
        open(writerObj);
        for rep = 1:6
            for b = 1:nBandsNir
                filename  = ['./figures/rhoRCAllvsAll_' sensor '_' num2str(bandsNir(b)) '.png'];
                thisimage = imread(filename);
                writeVideo(writerObj, thisimage);
            end
        end
        close(writerObj);
    end
end
%% PCA: Conceptualizacion con un conjunto simple
if plotFlag
    close all
    % Genero datos aleatorios en forma de gaussiana 2D:
    u = copularnd('Gaussian',0.89,1000);
    u = [u 2*u(:,1)];
    u = u.*[1 1.3 2];

    % Grafico los datos
    plot(u(:,1),u(:,2),'.')

    % Hallo la descomposicion por PCA
    [coeff, score, eigenVal] = pca(u);

    % Veo la pinta de los autovectores de la matriz de covarianza, puestos en 
    % columnas en la matriz "coeff", y les sumo la media de los datos:

    A = mean(u);
    figure
    hold on
    plot3(u(:,1),u(:,2),u(:,3),'.')
    plot3(A(1)+[-coeff(1,1) coeff(1,1)],A(2)+[-coeff(2,1) coeff(2,1)],A(3)+[-coeff(3,1) coeff(3,1)],'-r')
    plot3(A(1)+[-coeff(1,2) coeff(1,2)],A(2)+[-coeff(2,2) coeff(2,2)],A(3)+[-coeff(3,2) coeff(3,2)],'-g')
    plot3(A(1)+[-coeff(1,3) coeff(1,3)],A(2)+[-coeff(2,3) coeff(2,3)],A(3)+[-coeff(3,3) coeff(3,3)],'-b')
    daspect([1 1 1])
    hold off


    w = score*coeff' + A; % la forma de reconstruir los datos originales a
    % partir de la descomposicion por PCA

    % Comprobacion grafica de que la forma anterior es correcta:
    figure
    hold on
    plot(w(:,1),u(:,1),'.r')
    plot(w(:,2),u(:,2),'.g')
    plot(w(:,3),u(:,3),'.b')
    hold off
end

%% PCA: Compute eigenvectors and eigenvalues of the covariance matrix
for s = 1:length(sensors)

    sensor = sensors{s};
%     SENS.(sensor) = rmfield(SENS.(sensor),'PCA');
% end

    bNir = SENS.(sensor).bandsPcaNirIdx;
    nNir = length(bNir);
    bSwir = allSubsets(SENS.(sensor).bandsPcaBlackIdx,2);

    for bs0 = 1:length(bSwir)
        bs = bSwir{bs0};
        pcaModNum = ['M_' strrep(num2str(SENS.(sensor).bands(bs)),'  ','_')];

%         SENS.(sensor).PCA.(pcaModNum).nBands = length(bs) + 1;
        
        for bn0 = 1:length(bNir)
            bn  = bNir(bn0);

            nirBand = ['B_' num2str(SENS.(sensor).bands(bn))];
            
            bandsPca  = [bn bs];
            
            [coeff, score, eigenVal] = pca(SENS.(sensor).rhoRC(PCA.cond,bandsPca));
            pcaSuffix =  sprintf('_%.0f' , SENS.(sensor).bands(bandsPca));

            % los autovectores PCA puestos en columnas (1ero: mayor
            % varianza asociada).
            SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVec    = coeff;
            % (Se elimina la primera fila porque es la correspondiente a la
            % banda a corregir, y se elimina la ultima columna porque es el
            % autovector con menor peso asociado.
            SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVecR   = inv (coeff(2:end,1:(end-1)));
            % El condicional de la matriz es clave para evaluar la bondad
            % de la inversion. Suele empeorar a medida que nos alejamos al
            % azul, y es peor para el modelo de 3 bandas que para el de 2.
            SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVecRC  = cond(coeff(2:end,1:(end-1)));
            % Las proyecciones de los datos en las coordenadas de la base
            % de autovectores de la matriz de covarianza.
            SENS.(sensor).PCA.(pcaModNum).(nirBand).projec    = score;
            % Los autoval asociados (varianza asociada a cada autovalor)
            SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVal    = eigenVal;
            % Las medias: habra q sumarselas para reconstruir la senal.
            SENS.(sensor).PCA.(pcaModNum).(nirBand).RCmean    = mean(SENS.(sensor).rhoRC(PCA.cond,bandsPca));

            SENS.(sensor).PCA.(pcaModNum).(nirBand).bands     = SENS.(sensor).bands(bandsPca);
            SENS.(sensor).PCA.(pcaModNum).(nirBand).bandsID   = bandsPca;
            SENS.(sensor).PCA.(pcaModNum).(nirBand).title     = ['PCA(' sensor ')[' regexprep(num2str(SENS.(sensor).bands(bandsPca)), '  ', '-') ']'];
            SENS.(sensor).PCA.(pcaModNum).(nirBand).title2    = [sensor '_' regexprep(num2str(SENS.(sensor).bands(bandsPca)), '  ', '_')];
            if plotFlag
                disp([sensor ':'                                    newline ...
                    'NIR  bands: ' num2str(SENS.(sensor).bands(bn)) newline ...
                    'SWIR bands: ' num2str(SENS.(sensor).bands(bs))])
                disp('Eigenvectors:')
                disp(coeff)
                disp('Mean projections:')
                disp(mean(abs(score)))
                disp('Eigenvalues:')
                disp(eigenVal')
                disp('Inverse Model Matrix:')
                disp(SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVecR );
                disp('Inverse Model Matrix Conditional:')
                disp(SENS.(sensor).PCA.(pcaModNum).(nirBand).eigVecRC);
            end
        end
    end
end
save('PCA_eigen/PCA_allSensors','SENS')
%% PCA: Eigenvectors

% pcaEigenOption0 = [false];
pcaEigenOption0 = [true false];
cols = {'r';'g';'b';'m';'k'};
% true: multiplies PCA-eigenvector by corresp. eigenvalue
if plotFlag
    for pcaOpt = 1:2
        pcaEigenOption = pcaEigenOption0(pcaOpt);
        for s = 1:length(sensors)
            sensor         = sensors{s}                     ;
            bandsWave      = SENS.(sensor).bandsPca         ;
            waveExt        = [min(bandsWave) max(bandsWave)];
            sensorRhoRc    = SENS.(sensor).rhoRC(PCA.cond,:);
            models         = fieldnames(SENS.(sensor).PCA)  ;
            for nm = 1:length(models)
                model = SENS.(sensor).PCA.(models{nm});
                bands = fieldnames(model);
%                 for b = 1:length(bands)
%                     bands{b} = split(bands{b},'_');
%                     bands{b} = str2double(bands{b}{2});
%                 end
%                 bands = cell2mat(bands);

                figure
                [spDim, ~] = numSubplots(length(bands));

                legendFlag = true;

                for b = 1:length(bands)
                    
                    band2corr = model.(bands{b});
                    clear h hleg hleg0
                    subplot(spDim(1),spDim(2),b)
                    hold on
                    if pcaEigenOption
                        pcaFactor = band2corr.eigVal/band2corr.eigVal(1);
                    else
                        pcaFactor = ones(size(band2corr.eigVal));
                    end
                    for c = 1:length(band2corr.bands)
                        h   (c) = plot(band2corr.bands,pcaFactor(c)*sign(band2corr.eigVec(1,c))*band2corr.eigVec(:,c),['.-'  cols{c}],'markers',20);
                        hleg0{c} = ['PCA-' num2str(c)];
                    end
                    if legendFlag
                        hleg = legend(h,hleg0);
                        set(hleg,'Location','southeast')
                        set(hleg,'color','none');
                        set(hleg,'edgecolor','none');
                        legendFlag = false;
                    end                    
                    xlabel('Longitud de onda [nm]')
                    xlim(waveExt + 0.03*(waveExt(2)-waveExt(1))*[-1 1])
                    ylim([-1 1])
            %         set(gca,'Yscale','log')
                    set(gca,'XTick',band2corr.bands)
                    set(gca,'xgrid','on')
                    hold off
                    Figuras.sizes(16,16,2,2)

                    titStr = ['Autovectores PCA, sensor: ' sensor '-' replace(models{nm},'_','-')];
                    if pcaEigenOption
                        titStr  = [titStr newline 'PCA-eigenVec \propto PCA-eigenVal'];
                        titStr1 = 'TimesVal';
                    else
                        titStr1 = '';
                    end
                end
                mtit(titStr)
                Figuras.saveMaximized(closeFlag,['./figures/PCAEigenVec' titStr1 sensor '_' models{nm}])
            end
        end
    end
end
%% PCA: Reconstruct RC signal from PCA!!!
if plotFlag
	for s = 1:length(sensors)
        sensor         = sensors{s}                     ;
        bandsWave      = SENS.(sensor).bandsPca         ;
        waveExt        = [min(bandsWave) max(bandsWave)];
        sensorRhoRc    = SENS.(sensor).rhoRC(PCA.cond,:);
        
        models         = fieldnames(SENS.(sensor).PCA)  ;
        for nm = 1:length(models)
            legendFlag = true ;
            model = models{nm};
            bands = fieldnames(SENS.(sensor).PCA.(model));

            figure
            [spDim, ~] = numSubplots(length(bands));

            for b = 1:length(bands)
                clear h hleg hleg0
                band2corr   = SENS.(sensor).PCA.(models{nm}).(bands{b});
                [spDim, ~] = numSubplots(length(bands));
                subplot(spDim(1),spDim(2),b)
                hold on
                    nBands = length(band2corr.bands);
                    for c = 0:nBands
                        projec  = band2corr.projec;
                        projec(:,(c+1):nBands) = 0;
                        % Esta formula de "rebuild" esta chequeado en el
                        % ejemplo de la gaussiana 2D (mas arriba)
                        % A su vez, ver el help de pca...
                        rebuild = projec*(band2corr.eigVec)' + band2corr.RCmean;
                        origin  = sensorRhoRc(:,band2corr.bandsID);
                        dOrgReb = (origin-rebuild);%./origin;
            %                 plot(model.bandsWave,prctile(abs(dOrgReb),75),['.--' cols{c+1}])
                        h    (c+1) = plot(band2corr.bands,max   (abs(dOrgReb)    ),['.-'  cols{c+1}],'markers',20);
                        hleg0{c+1} = [num2str(c) ' comp'];
                    end
                    xlim(waveExt+0.03*(waveExt(2)-waveExt(1))*[-1 1])
                    ylim([-0.01 0.45])
            %         set(gca,'Yscale','log')
                    if mod(b,spDim(2))==1 && mod(b,spDim(1))==2
                        ylabel(['Máximo error absoluto' newline 'max(|RC-PCA|)'])
                    end
                    xlabel('Longitud de onda [nm]')
                    set(gca,'XTick',band2corr.bands)
                    set(gca,'xgrid','on')
                hold off
                Figuras.sizes(16,16,2,2)    
            end
            if legendFlag
                hleg = legend(h,hleg0);
                set(hleg,'Location','southeast')
                set(hleg,'color','none');
                set(hleg,'edgecolor','none');
                legendFlag = false;
            end
            titStr = ['Sensor: ' sensor '-' replace(models{nm},'_','-')];
            mtit(titStr)

            Figuras.sizes(16,16,2,2)    
            Figuras.saveMaximized(closeFlag,['./figures/PCAreconstructSOS_blackOcean_' sensor '_' models{nm}])
        end
	end
end
spare = 0;
%% PCA: Inversion scheme (applied to scenarios with rhoW = 0)(vectorized)
rhoRange = [-0.1 0.3];
for s = 1:length(sensors)
    sensor         = sensors{s}                           ;
    nMod           = length(fieldnames(SENS.(sensor).PCA));

    [spDim, ~]     = numSubplots(nMod);


    models         = fieldnames(SENS.(sensor).PCA)  ;

    bands = SENS.(sensor).bandsPcaNir;
    for b = 1:length(bands)
        legendFlag = true ;

        if plotFlag
            figure
        end
        for nm = 1:length(models)
            clear h hleg hleg0
            %%%%%%%%%%%%%%%%%%%%%%%%%% INVERSION PCA %%%%%%%%%%%%%%%%%%%%%%%%%%
            % band2corr: estructura con los resultados de PCA para banda a 
            % corregir "bands(b)" y bandas correctoras, explicitadas segun
            % el modelo "models{nm}"...
            band2corr = SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]);
            % subset con las rhoRC no afectadas por sunglint elevado, solo
            % las bandas a corregir y correctoras:
            tSet      = SENS.(sensor).rhoRC(PCA.cond,band2corr.bandsID)';
            
            % Proyecciones:
            % estas cuentas fueron chequeadas con las del cuaderno:
            aInv    = band2corr.eigVecR*(tSet(2:end,:) -   band2corr.RCmean(2:end)');
            nirRC   = band2corr.eigVec(1,1:(end-1))*aInv + band2corr.RCmean(1)      ;
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            X = tSet(1,:)'; % la banda a corregir es la primera
            Y = nirRC';
            mae0  = mean(abs(X-Y));
            mdl   = fitlm(X,Y);
            bias  = table2array(mdl.Coefficients(1,1));
            slope = table2array(mdl.Coefficients(2,1));
            r2    = mdl.Rsquared.Ordinary;

            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).predicted = X;
            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).observed  = Y;
            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).mae0  = mae0 ;
            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).bias  = bias ;
            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).slope = slope;
            SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).r2    = r2   ;                

            stStr = ['Y = ' sprintf('%0.4f',slope) 'X' sprintf('%+0.4f',bias) newline ...
                     'R^{2} = ' sprintf('%0.4f',r2)                            newline ...
                     'MAE = ' sprintf('%0.5f',mae0)];
            if plotFlag
                [spDim, ~] = numSubplots(length(models));
                subplot(spDim(1),spDim(2),nm)
                hold on
                    plot(rhoRange,rhoRange,'--k')
                    plot(rhoRange,slope*rhoRange+bias,'r')
                    densityPlotJ(X,Y,256,3)
                hold off
                text(0.01,0.8,stStr,'color','r','units','normalized')
                title([sensor ': ' replace(models{nm},'_','-')])
                Figuras.sizes(16,16,2,1)
                daspect([1 1 1])
                xlim(rhoRange); ylim(rhoRange);
                xlabel(['\rho_{a}^{SOS}(' num2str(band2corr.bands(1)) ')'])
                ylabel(['\rho_{a}^{PCA}(' num2str(band2corr.bands(1)) ')'])
            end
        end
        if plotFlag
            Figuras.saveMaximized(closeFlag,['./figures/PCAvsSOS_blackOcean_' sensor '-' num2str(bands(b))])
        end
    end
end
%% VIDEO

%% Videos with scatter plots
if plotFlag
    for s = 1:length(sensors)
        disp(['Creating video for: ' sensors{s}])
        sensor = sensors{s};
        bandsNir     = SENS.(sensor).bandsPcaNir;
        nBandsNir    = length(bandsNir);
        writerObj = VideoWriter(['./figures/PCAvsSOS_blackOcean_' sensor '.avi']);
        writerObj.FrameRate = 2;
        open(writerObj);
        for rep = 1:6
            for b = 1:nBandsNir
                filename  = ['./figures/PCAvsSOS_blackOcean_' sensor '-' num2str(bandsNir(b)) '.png'];
                thisimage = imread(filename);
                writeVideo(writerObj, thisimage);
            end
        end
        close(writerObj);
    end
end

%% Conditional numbers: plot
magnitudes      = {'slope';'bias';'r2';'mae0';'eigVecRC'};
magnitudesLabel = {'PENDIENTE';'SESGO';'R^{2}';'MAE';['Condicional' newline 'de la Matriz de Inversión']};

cols = {'r';'g';'b';'m'};

if plotFlag
    for s = 1:length(sensors)
        figure
        sensor = sensors{s};
        bands = SENS.(sensor).bandsPcaNir;

        models = fieldnames(SENS.(sensor).PCA);
        nMod   = length(models);

        mag    = zeros(length(bands),1);

        clear h hleg

        [spDim, ~] = numSubplots(length(magnitudes));
        for m = 1:length(magnitudes)
            subplot(spDim(1),spDim(2),m)
                hold on
                for nm = 1:nMod
                    for b = 1:length(bands)
                        mag(b) = SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]).(magnitudes{m});
                    end
                    h(nm)    = plot(bands,mag,[ '.-' cols{nm}]);
                    hleg{nm} = replace(models{nm},'_','-');
                end
                xlabel('Longitud de onda [nm]')
                ylabel(magnitudesLabel{m})
                if m == 1
                    legend(h,hleg,'location','southeast')
                end
                hold off
                box on
                set(gca,'yscale','log')
        end
        mtit(sensor)
        Figuras.sizes(16,16,2,1)
        if plotFlag
            Figuras.saveMaximized(closeFlag,['./figures/PCA_Retrievals_' sensor])
        end
    end
end
%%
