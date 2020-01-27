%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% rhoW != 0 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%
clc
clear
load('SOS_PCA_blackOcean.mat')
plotFlag = false;
closeFlag = true;

sensors = {'MA';'MT';'VIIRS';'MSI';'SMAR'};


NS = length(sensors);
%% Load DATA
variW = load('SOSSEP2019_non00_vari');
variW = variW.vari;

stFlag = true; st0 = 0;

while stFlag
    st0 = st0 + 1;
    st = sprintf('%02d',st0);
    try
        rho0 = load(['SOSSEP2019_' st]);
        rho0 = rho0.rho;
        ASD.(['ST_' st]).rhot = rho0;
    catch
        disp(['Total stations = ' num2str(st0-1)])
        stFlag = false;
        NW = st0 - 1;
    end
end
%% Load SNRs
snrPath = '/home/gossn/Dropbox/Documents/inSitu/Database/SRFs';
for s = 1:NS
    sensor = sensors{s};
    SENS.(sensor).SIG = xlsread([snrPath '/SNR_' sensor '.xlsx']);
end

%% Transmitancia directa: tRay (unicamente componente Rayleigh)

% sensors = {'MA';'MT'};

ancillaryPath = '/home/gossn/Dropbox/Documents/ancillary/global/';
tRay = load([ancillaryPath 'hyperspectral_rayleigh']);

lambdaRay = tRay(:,1);
depolRay  = tRay(:,3);
tRay      = tRay(:,2);

for s = 1:NS
    sensor         = sensors{s};
    
    [~,rhoBand] = hyp2satBands(lambdaRay,tRay,sensor);
    SENS.(sensor).transmittance.Rayleigh = rhoBand;

    [~,rhoBand] = hyp2satBands(lambdaRay,depolRay,sensor);
    SENS.(sensor).transmittance.Depol    = rhoBand;
end
%% Transmitancia directa: tAer (unicamente componente de aerosoles)

lambdaAer = lambdaRay;
tAer      = 0.0600*(lambdaAer/500).^(-1.0); % Valor de 0.04 reportado en el proceeding
% tAer      = 0.0675*(lambdaAer/450).^(-0.2);
% tAer      = 0.4000*(lambdaAer/450).^(-0.0);

for s = 1:NS
    sensor         = sensors{s};
    
    [~,rhoBand] = hyp2satBands(lambdaAer,tAer,sensor);
    SENS.(sensor).transmittance.Aerosol = rhoBand;
end

%% Transmitancia directa: AIR MASS FACTOR

muW = 1./cosd(variW(:,strcmp(varlab,'zenith_sol'))) + ...
      1./cosd(variW(:,strcmp(varlab,'zenith_obs')));

for s = 1:NS

    sensor    = sensors{s};
    tRayS     = SENS.(sensor).transmittance.Rayleigh;
    tAerS     = SENS.(sensor).transmittance.Aerosol;

    SENS.(sensor).transmittance.tRayAer = exp(-(0.52*tRayS' + 5/6*tAerS')*muW')';
end

%% Transmitancia directa: unos plots
close all

if plotFlag
    
    NCol = 1024;
	NatmW = size(variW,1);
    colMap = parula(NCol);
    colMuWidx = round((muW-min(muW))/(max(muW)-min(muW))*(1024-1) + 1);
    colMuW = colMap(colMuWidx,:);
    
    xRange = [min(lambdaRay) max(lambdaRay)];

    sp = 0;
    for s = 1:NS

        sensor    = sensors{s};
        tRayS     = SENS.(sensor).transmittance.Rayleigh;
        tAerS     = SENS.(sensor).transmittance.Aerosol;
        lambdaS   = SENS.(sensor).bands;

        sp = sp + 1;
        subplot(2,3,sp)
        hold on
            plot(lambdaRay,tRay,'-b')
            plot(lambdaAer,tAer,'-g')
            plot(lambdaS,tRayS,'.b','markers',20)
            plot(lambdaS,tAerS,'.g','markers',20)
        hold off
        set(gca,'yscale','log')
    %     set(gca,'xscale','log')
        xlim(xRange)
        xlabel('Longitud de onda [nm]')
        ylabel('Espesor óptico')
        title(['Sensor: ' sensor])
        box on
    end
    legend('Rayleigh molecular, \tau_{Ray}','Aerosoles, \tau_{Aer}')
    Figuras.sizes(15,15,2,1)
    Figuras.saveMaximized(closeFlag,'./figures/transmittance')

    for s = 1:NS
        sensor    = sensors{s};
        subplot(2,3,s)
        hold on
        for atm = 1:NatmW
            plot(SENS.(sensor).bands,SENS.(sensor).transmittance.tRayAer(atm,:),'color',colMuW(atm,:),'markers',10)
        end
        hold off
        if s == NS
            p = get(gca,'position');
            clbr = colorbar;
            clbr.YTick      = linspace(0,1,5);
            clbr.YTickLabel = 0.01*round(100*linspace(min(muW),max(muW),5));
            ylabel(clbr,'Factor de masa de aire')
            set(gca,'Position',p)
        end
        xlim([380 2000])
        ylim([0.5 1])
        xlabel('Longitud de onda [nm]')
        ylabel('Factor de transmitancia')
        title(['Sensor: ' sensor])
        legend('off')
        Figuras.sizes(15,15,2,1)
    end
    Figuras.saveMaximized(closeFlag,'./figures/transmittance')
end
%% SRFs: Convolute rhoW(ASD)

ASDw = xlsread('ASD_overpasses_20190926_matlab.xlsx');
lambdasASD = ASDw(:,1)'; 
rhow = ASDw(:,(1:NW)+1)'; % la primera columna son las longitudes de onda
for s = 1:length(sensors)
    sensor = sensors{s};
    [waveBandMean,rhoBand] = hyp2satBands(lambdasASD',rhow',sensor);
    for st0 = 1:NW
        st = sprintf('%02d',st0);
        SENS.(sensor).ASD.rhow.( ['ST_' st]) =    rhow(st0,:);
        SENS.(sensor).ASD.rhowB.(['ST_' st]) = rhoBand(st0,:);
        SENS.(sensor).ASD.rhowB_mat(st0,:)   = rhoBand(st0,:);        
    end
end
spare = 0;

%% Obtengo las reflectancias a TOA por banda (convolucionando con las SRFs de cada sensor)

for s = 1:length(sensors)
    sensor = sensors{s};
    for st0 = 1:NW
        st = sprintf('%02d',st0);
        rhot = ASD.(['ST_' st]).rhot;
        [waveBandMean,rhoBand] = hyp2satBands(lambdas',rhot',sensor);
        SENS.(sensor).ASD.rhot.( ['ST_' st]) = rhot;
        SENS.(sensor).ASD.rhotB.(['ST_' st]) = rhoBand;
    end
end
spare = 0;

%% RC: rho(ASD+SOS)

%%%% correspondencia entre parametros de entrada 
% de rho(SOS,rhow=ASD) y rho(SOS,rhow=0) para efectuar la Rayleigh Correction.

% Matcheo entre parametros atmosfericos de los conjuntos de simulaciones
% a rhoW = 0 y a rhoW != 0

for leg = 1:length(varlab)
    varStr = varlab{leg};
    varIdx.(varStr).idx  = find(strcmp(varlab,varStr));
end

varIdx.void.cond       =  0;
varIdx.w.cond          = -1; % si es -1, tiene que ser igual
varIdx.mod_aer.cond    =  1;
varIdx.tau_aer.cond    =  0;
varIdx.zenith_sol.cond = -1;
varIdx.zenith_obs.cond = -1;
varIdx.phi_obs.cond    = -1;


condRC  = true( size(variW,1),size(vari,1));
condRC2 = zeros(size(variW,1),1);
for atm = 1:size(variW,1)
    for leg = 1:length(varlab)
        if varIdx.(varlab{leg}).cond == -1
            cond0 = vari(:,varIdx.(varlab{leg}).idx) == variW(atm,varIdx.(varlab{leg}).idx);
        else
            cond0 = vari(:,varIdx.(varlab{leg}).idx) == varIdx.(varlab{leg}).cond;
        end
        condRC(atm,:) = condRC(atm,:) & cond0';
    end
    condRC2(atm) = find(condRC(atm,:));
end
% COMPROBACION
% atm = 0; flag = true;
% while flag
%     atm = atm + 1;
%     if all(variW(atm,[1 2 5 6 7]) == vari(condRC2(atm),[1 2 5 6 7]))
%         spare = 0;
%     else
%         flag = false;
%     end
% end
%% RHO RAYLEIGH por sensor

rhoRAY = rho(:,condRC2)';

SG.glintedW = SG.glinted(condRC2);

for s = 1:length(sensors)
    sensor = sensors{s};
    [waveBandMean,rhoBand] = hyp2satBands(lambdas',rhoRAY',sensor);
    SENS.(sensor).ASD.rhoRayleighW = rhoBand;
end
%% RC: rhoRC(ASD+SOS)

% for s = 1:NS
%     sensor = sensors{s};
%     SENS.(sensor).ASD = rmfield(SENS.(sensor).ASD,'rhorcB');
% end
MC = 30;
for s = 1:length(sensors)
    sensor = sensors{s};
	y   = SENS.(sensor).ASD.rhoRayleighW;
    sig = SENS.(sensor).SIG(:,3);
    if MC == 1
        sig = 0*sig;
    end
    for st0 = 1:NW
        st = sprintf('%02d',st0);
        SENS.(sensor).ASD.rhorcB.(['ST_' st]) = zeros(size(y,1),size(y,2),MC);
        x = SENS.(sensor).ASD.rhotB.( ['ST_' st]);
        for mc = 1:MC
            xmc = x+randn(size(x)).*sig';
            SENS.(sensor).ASD.rhorcB.(['ST_' st])(:,:,mc) = xmc-y;
        end
    end
end
%% INVERSION PCA (rhoW != 0)
for s = 1:length(sensors)
    sensor = sensors{s}                   ;
    models = fieldnames(SENS.(sensor).PCA);

    bands = SENS.(sensor).bandsPcaNir;
	for nm = 1:length(models)
%         SENS.(sensor).ASD.PCA.(models{nm}).rhowperc
%         SENS.(sensor).ASD.PCA.(models{nm}).rhowperc = rmfield(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc,'IQR');
        for st0 = 1:NW
            st = sprintf('%02d',st0);
%             disp([sensor ' ' models{nm} ' ' st])
            rhoRC = SENS.(sensor).ASD.rhorcB.(['ST_' st]);
            rhoPCA = rhoRC;
            for b = 1:length(bands)
                %%%%%%%%%%%%%%%%%%%%%%%%%% INVERSION PCA %%%%%%%%%%%%%%%%%%%%%%%%%%
                band2corr = SENS.(sensor).PCA.(models{nm}).(['B_' num2str(bands(b))]);
                % calculo rhoATMPCA para todos! Despues evaluo los que tienen glint!
                for mc = 1:MC
                    tSet    = permute(SENS.(sensor).ASD.rhorcB.(['ST_' st])(:,band2corr.bandsID,mc),[2 1 3]);
                    aInv    = band2corr.eigVecR*(tSet(2:end,:,:) - band2corr.RCmean(2:end)');
                    nirRC   = band2corr.eigVec(1,1:(end-1))*aInv + band2corr.RCmean(1)    ;
                    rhoPCA(:,b,mc) = nirRC;
                end
            end
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            % %% Test Permute and reshape
            % clear A
            % clc
            % for i = 1:4
            %     for j = 1:6
            %         for k = 1:8
            %             A(i,j,k) = (100*i+10*j+k);
            %         end
            %     end
            % end
            % 
            % B = permute(A,[3 1 2]);
            % 
            % C = reshape(A,24,8)

            SENS.(sensor).ASD.PCA.(models{nm}).rhoatm.(['ST_' st]) = rhoPCA;

            % computar trhow!!

            rhoRC = SENS.(sensor).ASD.rhorcB.(['ST_' st]);
            SENS.(sensor).ASD.PCA.(models{nm}).trhow.(['ST_' st]) = rhoRC - rhoPCA;

            % computar rhow!!
            td = SENS.(sensor).transmittance.tRayAer;
            rhowPCA = (rhoRC - rhoPCA)./td;
            
            SENS.(sensor).ASD.PCA.(models{nm}).rhow.(['ST_' st]) = rhowPCA;
            
            for pr0 = [5 25 50 75 95]
                pr = sprintf('%0.2d',pr0);
                rpca = rhowPCA(~ SG.glintedW,:,:);
                rpca = permute(rpca,[3 1 2]);
                rpca = reshape(rpca,numel(rpca(:,:,1)),numel(rpca(1,1,:)));
                SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.(['P' num2str(pr)]).(['ST_' st])    = prctile(rpca,pr0);
                SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.(['P' num2str(pr) '_mat'])(st0,:) = prctile(rpca,pr0);
            end
%             SENS.(sensor).ASD.PCA.(models{nm}).rhowperc = rmfield(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc,'IQR');
            SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.IQR_mat(st0,:) = prctile(rpca,75) - prctile(rpca,25);
            SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.max_mat(st0,:) = max(rpca);
            SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.min_mat(st0,:) = min(rpca);
        end

        for pr0 = [5 25 50 75 95]
            pr = sprintf('%0.2d',pr0);
            SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.(['P' num2str(pr) '_mat']) = ...
            squeeze(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.(['P' num2str(pr) '_mat']));
        end
        SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.IQR_mat = ...
        squeeze(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.IQR_mat);
        SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.max_mat = ...
        squeeze(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.max_mat);
        SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.min_mat = ...
        squeeze(SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.min_mat);
    end
end
%% Resultados
for s = 1:length(sensors)
    sensor = sensors{s}                   ;
    models = fieldnames(SENS.(sensor).PCA);

    bands = SENS.(sensor).bandsPcaNir;
    for b = 1:length(bands)
        X    = SENS.(sensor).ASD.rhowB_mat(:,b);
        axLim = [min(X)*(1-0.5*(max(X) - min(X))) max(X)*(1+0.5*(max(X) - min(X)))];
        for nm = 1:length(models)
            [spDim, ~] = numSubplots(length(models));
            Y    = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.P50_mat(:,b);
            Ym   = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.P25_mat(:,b);
            Yp   = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.P75_mat(:,b);
            Yerr = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.IQR_mat(:,b);
            YMax = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.max_mat(:,b);
            YMin = SENS.(sensor).ASD.PCA.(models{nm}).rhowperc.min_mat(:,b);
            
            out = linearFitJG(X,Y,Yerr,100);
            SENS.(sensor).ASD.PCA.(models{nm}).(['stats_' num2str(bands(b))]) = out.mean;
            
            if plotFlag
                subplot(spDim(1),spDim(2),nm)
                hold on
                plot(X,Y,'.r','markers',10)
                hLinear = plot(X,out.mean.m*X+out.mean.b,'-k');
                hRef    = refline(1,0);
                for st = 1:NW
                    plot([X(st) X(st)],[Ym(st) Yp(st)],'-r','LineWidth',2)
                end
                hold off

%                 stStr = ['Y = '    sprintf('%0.4f',out.mean.m) 'X' sprintf('%+0.4f',out.mean.b) newline ...
%                         'R^{2} = ' sprintf('%0.4f',out.mean.R)                                  newline ...
%                         'RMSE = '  sprintf('%0.4f',out.mean.RMSE)                               newline ...
%                         'MAE = '   sprintf('%0.4f',out.mean.MAE)];

                stStr = ['Y = '    sprintf('%0.4f',out.mean.m) 'X' sprintf('%+0.4f',out.mean.b) newline ...
                        'R^{2} = ' sprintf('%0.4f',out.mean.R)];
                axis([axLim axLim])
                xlabel(['\rho_{w}^{ASD}[' num2str(bands(b)) ']'])
                ylabel(['\rho_{w}^{PCA}[' num2str(bands(b)) ']'])
                title([sensor '-' replace(replace(models{nm},'_','-'),'M','PCA')])
                daspect([1 1 1])
                lgnd = legend([hLinear],{stStr},'FontSize',12);
                set(lgnd,'Location','northwest');                
                set(lgnd,'color','none');
                set(lgnd,'box','off');
                Figuras.sizes(15,15,2,1)
            end
        end
        if plotFlag
            Figuras.saveMaximized(closeFlag,['./figures/rhoW_Tc_' sensor '_band_'  num2str(bands(b)) '_MC_' num2str(MC)])
        end
    end
end
%% Resultados: estadisticos

magnitudes      = {'slope';'bias';'r2';'mae0';'eigVecRC'};
magnitudesLabel = {'SLOPE';'BIAS';'R^{2}';'MAE';'RMSE';'MAE';'Cond(Inversion Matrix)'};

stats = struct('Slope', 'm', 'Bias', 'b', 'R2', 'R', 'MAE', 'MAE', 'RMSE', 'RMSE', 'MAD', 'MAD');
statsLabel = fieldnames(stats);
statsRanges = [0.3 1.1; ...
               -0.05 0.25; ...
               10^-2 10^0; ...
               10^-5 10^0; ...
               10^-3 10^0; ...
               10^-4 10^0];


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

        [spDim, ~] = numSubplots(length(statsLabel));
        for stat = 1:length(statsLabel)
            subplot(spDim(1),spDim(2),stat)
                hold on
                for nm = 1:nMod
                    for b = 1:length(bands)
                        mag(b) = SENS.(sensor).ASD.PCA.(models{nm}).(['stats_' num2str(bands(b))]).(stats.(statsLabel{stat}));
                    end
                    h(nm)    = plot(bands,mag,[ '.-' cols{nm}]);
                    hleg{nm} = replace(models{nm},'_','-');
                    ylim(statsRanges(stat,:))
                end
                xlabel('Wavelength [nm]')
                ylabel(statsLabel{stat})
                if stat == 1
                    legend(h,hleg,'location','southeast')
                end
                hold off
                box on
                if ~ strcmp(statsLabel{stat},'Bias')
                    set(gca,'yscale','log')
                end
        end
        mtit(sensor)
        Figuras.sizes(16,16,2,1)
        if plotFlag
            Figuras.saveMaximized(closeFlag,['./figures/PCA_Retrievals_RHOW_' sensor '_MC_' num2str(MC)])
        end
    end
end
%%