from sklearn.decomposition import PCA
import pandas as pd
import re
import numpy as np
from bioinfokit.visuz import screeplot, pcaplot, general
from itertools import groupby, chain
import string
import sys, csv
import matplotlib.pyplot as plt
import scipy.stats as stats
from tabulate import tabulate
from termcolor import colored
from statsmodels.graphics.mosaicplot import mosaic
from textwrap3 import wrap
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.formula.api import ols
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from decimal import Decimal


def seqcov(file="fastq_file", gs="genome_size"):
    x = fastq_format_check(file)
    if x == 1:
        print("Error: Sequences are not in fastq format")
        sys.exit(1)
    num_reads, total_len = fqreadcounter(file)
    # haploid genome_size must be in Mbp; convert in bp
    gs = gs * 1e6
    cov = round(float(total_len / gs), 2)
    print("Sequence coverage for", file, "is", cov)

def mergevcf(file="vcf_file_com_sep"):
    vcf_files = file.split(",")
    merge_vcf = open("merge_vcf.vcf", "w+")
    file_count = 0
    print("merging vcf files...")
    for f in vcf_files:
        if file_count == 0:
            read_file = open(f, "rU")
            for line in read_file:
                merge_vcf.write(line)
            read_file.close()
        elif file_count > 0:
            read_file = open(f, "rU")
            for line in read_file:
                if not line.startswith("#"):
                    merge_vcf.write(line)
            read_file.close()
        file_count += 1
    merge_vcf.close()


def pca(table="p_df"):
    d = pd.DataFrame(data=table)
    d_cols = list(d.columns.values)
    pca_out = PCA()
    pca_out.fit(d)
    prop_var = pca_out.explained_variance_ratio_
    cum_prop_var = np.cumsum(prop_var)
    rotation = pca_out.components_
    num_pc = pca_out.n_features_
    pc_list = list(range(1, num_pc+1))
    pc_list = ["PC"+str(w) for w in pc_list]
    pca_df_var = [prop_var, cum_prop_var]
    pca_df_out = pd.DataFrame.from_dict(dict(zip(pc_list, zip(*pca_df_var))))
    pca_df_rot_out = pd.DataFrame.from_dict(dict(zip(pc_list, rotation)))
    pca_df_out.rename(index={0: "Proportion of Variance", 1: "Cumulative proportion"}, inplace=True)
    print("Component summary\n")
    print(pca_df_out)
    print("\nLoadings\n")
    pca_df_rot_out['sample'] = d_cols
    pca_df_rot_out = pca_df_rot_out.set_index('sample')
    del pca_df_rot_out.index.name
    print(pca_df_rot_out)
    pcascree = [pc_list, prop_var]
    # screeplot
    screeplot(obj=pcascree)
    # for pcaplot; take PC1 and PC2 loadings
    pcaplot(x=rotation[0], y=rotation[1], z=rotation[2], labels=d_cols, var1=round(prop_var[0]*100, 2), var2=round(prop_var[1]*100, 2),
            var3=round(prop_var[2] * 100, 2))


def extract_seq(file="fasta_file", id="id_file"):
    # extract seq from fasta file based on id match
    id_list = []
    id_file = open(id, "rU")
    out_file = open("output.fasta", 'w')
    for line in id_file:
        id_name = line.rstrip('\n')
        id_list.append(id_name)
    list_len = len(id_list)
    value = [1] * list_len
    # id_list converted to dict for faster search
    dict_list = dict(zip(id_list, value))
    fasta_iter = fasta_reader(file)
    for record in fasta_iter:
        fasta_header, seq = record
        if fasta_header.strip() in dict_list.keys():
            out_file.write(">"+fasta_header+"\n"+seq+"\n")
    out_file.close()
    id_file.close()


# remove seqs which match to ids in id file
def extract_seq_nomatch(file="fasta_file", id="id_file"):
    # extract seq from fasta file based on id match
    id_list = []
    id_file = open(id, "rU")
    out_file = open("output.fasta", 'w')
    for line in id_file:
        id_name = line.rstrip('\n')
        id_list.append(id_name)
    list_len = len(id_list)
    value = [1] * list_len
    # id_list converted to dict for faster search
    dict_list = dict(zip(id_list, value))
    fasta_iter = fasta_reader(file)
    for record in fasta_iter:
        fasta_header, seq = record
        if fasta_header.strip() not in dict_list.keys():
            out_file.write(">"+fasta_header+"\n"+seq+"\n")
    out_file.close()
    id_file.close()

def fqreadcounter(file="fastq_file"):
    read_file = open(file, "rU")
    num_lines = 0
    total_len = 0
    for line in read_file:
        num_lines += 1
        header_1 = line.rstrip()
        read = next(read_file).rstrip()
        len_read = len(read)
        total_len += len_read
        header_2 = next(read_file).rstrip()
        read_qual = next(read_file).rstrip()
    read_file.close()
    num_reads = num_lines/4
    return num_reads, total_len


def fasta_reader(file="fasta_file"):
    read_file = open(file, "rU")
    fasta_iter = (rec[1] for rec in groupby(read_file, lambda line: line[0] == ">"))
    for record in fasta_iter:
        fasta_header = record .__next__()[1:].strip()
        fasta_header = re.split("\s+", fasta_header)[0]
        seq = "".join(s.strip() for s in fasta_iter.__next__())
        yield (fasta_header, seq)

def rev_com(seq=None, file=None):
    if seq is not None:
        rev_seq = seq[::-1]
        rev_seq = rev_seq.translate(str.maketrans("ATGCUN", "TACGAN"))
        return rev_seq
    elif file is not None:
        out_file = open("output_revcom.fasta", 'w')
        fasta_iter = fasta_reader(file)
        for record in fasta_iter:
            fasta_header, seq = record
            rev_seq = seq[::-1]
            rev_seq = rev_seq.translate(str.maketrans("ATGCUN", "TACGAN"))
            out_file.write(">" + fasta_header + "\n" + rev_seq + "\n")
        out_file.close()

# extract subseq from genome sequence
def ext_subseq(file="fasta_file", id="chr", st="start", end="end", strand="plus"):
    fasta_iter = fasta_reader(file)
    for record in fasta_iter:
        fasta_header, seq = record
        if id == fasta_header.strip() and strand == "plus":
            # -1 is necessary as it counts from 0
            sub_seq = seq[int(st-1):int(end)]
            print(sub_seq)
        elif id == fasta_header.strip() and strand == "minus":
            seq = rev_com(seq)
            sub_seq = seq[int(st-1):int(end)]
            print(sub_seq)

def fastq_format_check(file="fastq_file"):
    read_file = open(file, 'rU')
    x = 0
    for line in read_file:
        header = line.rstrip()
        if not header.startswith('@'):
            x = 1
        else:
            x = 0
        break
    return x

def tcsv(file="tab_file"):
    tab_file = csv.reader(open(file, 'r'), dialect=csv.excel_tab)
    csv_file = csv.writer(open('out.csv', 'w', newline=''), dialect=csv.excel)

    for record in tab_file:
        csv_file.writerow(record)

def ttsam(df='dataframe', xfac=None, res=None, evar=True):
    general.depr_mes("bioinfokit.visuz.stat.ttsam")

def chisq(table="table"):
    general.depr_mes("bioinfokit.visuz.stat.chisq")

class fastq:
    def __init__(self):
        pass

    def fastq_format_check(file="fastq_file"):
        read_file = open(file, 'rU')
        x = 0
        for line in read_file:
            header = line.rstrip()
            if not header.startswith('@'):
                x = 1
            else:
                x = 0
            break
        return x

    def detect_fastq_variant(file="fastq_file"):
        count = 0
        check = []
        fastq_file = open(file, 'rU')

        for line in fastq_file:
            header_1 = line.rstrip()
            read = next(fastq_file).rstrip()
            header_2 = next(fastq_file).rstrip()
            read_qual_asc = next(fastq_file).rstrip()
            asc_list = list(read_qual_asc)
            asc_list = list(map(ord, asc_list))
            min_q = min(asc_list)
            max_q = max(asc_list)
            check.append(min_q)
            check.append(max_q)
            count += 1
            if count == 40000:
                break
        fastq_file.close()
        min_q = min(check)
        max_q = max(check)
        if 64 > min_q >= 33 and max_q == 74:
            return 1
        elif min_q >= 64 and 74 < max_q <= 104:
            return 2
        elif 64 > min_q >= 33 and max_q <= 73:
            return 3


class format:
    def __init__(self):
        pass

    def fqtofa(file="fastq_file"):
        x = fastq_format_check(file)
        if x == 1:
            print("Error: Sequences are not in sanger fastq format")
            sys.exit(1)

        read_file = open(file, "rU")
        out_file = open("output.fasta", 'w')
        for line in read_file:
            header_1 = line.rstrip()
            read = next(read_file).rstrip()
            header_2 = next(read_file).rstrip()
            read_qual = next(read_file).rstrip()
            out_file.write(header_1+"\n"+'\n'.join(wrap(read, 60))+"\n")
        read_file.close()

    def tabtocsv(file="tab_file"):
        tab_file = csv.reader(open(file, 'r'), dialect=csv.excel_tab)
        csv_file = csv.writer(open('output.csv', 'w', newline=''), dialect=csv.excel)

        for record in tab_file:
            csv_file.writerow(record)

    def csvtotab(file="csv_file"):
        csv_file = csv.reader(open(file, 'r'), dialect=csv.excel)
        tab_file = csv.writer(open('output.txt', 'w', newline=''), dialect=csv.excel_tab)

        for record in csv_file:
            tab_file.writerow(record)

    def hmmtocsv(file="hmm_file"):
        hmm_file = open(file, "rU")
        csv_file = open("ouput_hmm.csv", "w")

        for line in hmm_file:
            line = line.strip()
            if not line.startswith("#"):
                data = re.split(' +', line)
                if len(data) == 19:
                    data[18] = data[18].replace(',', ' ')
                    csv_file.write(str.join(',', data))
                    csv_file.write("\n")
                elif len(data) > 19:
                    ele = list(range(18, len(data)))
                    data[18] = " ".join([e for i, e in enumerate(data) if i in ele])
                    data[18] = data[18].replace(',', '')
                    csv_file.write(str.join(',', data[0:19]))
                    csv_file.write("\n")
        hmm_file.close()
        csv_file.close()

    # find sanger fastq phred quality encoding format
    def fq_qual_var(file=None):
        if file is None:
            print("Error: No sanger fastq file provided")
            sys.exit(1)
        x = fastq.fastq_format_check(file)
        if x == 1:
            print("Error: Sequences are not in sanger fastq format")
            sys.exit(1)

        qual_format = fastq.detect_fastq_variant(file)

        if qual_format == 1:
            print("The fastq quality format is illumina 1.8+ (Offset +33)")
        elif qual_format == 2:
            print("The fastq quality format is illumina 1.3/1.4 (Offset +64)")
        elif qual_format == 3:
            print("The fastq quality format is Sanger (Offset +33)")
        else:
            print("\nError: Wrong quality format\n")
            sys.exit(1)


class stat():
    def oanova(table="table", res=None, xfac=None, ph=False, phalpha=0.05):
        # create and run model
        model = ols('{} ~ C({})'.format(res, xfac), data=table).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)

        # treatments
        # this is for bartlett test
        levels = table[xfac].unique()
        fac_list = []
        data_summary = []
        for i in levels:
            temp_summary = []
            temp = table.loc[table[xfac]==i, res]
            fac_list.append(temp)
            temp_summary.append(i)
            temp_summary.extend(temp.describe().to_numpy())
            data_summary.append(temp_summary)

        print("\nTable Summary\n")
        print(tabulate(data_summary, headers=["Group", "Count", "Mean", "Std Dev", "Min", "25%", "50%", "75%", "Max"]), "\n")

        # check assumptions
        # Shapiro-Wilk  data is drawn from normal distribution.
        w, pvalue1 = stats.shapiro(model.resid)
        w, pvalue2 = stats.bartlett(*fac_list)
        if pvalue1 < 0.05:
            print("Warning: Data is not drawn from normal distribution")
        else:
            # samples from populations have equal variances.
            if pvalue2 < 0.05:
                print("Warning: treatments do not have equal variances")

        print("\nOne-way ANOVA Summary\n")
        print(anova_table)
        print("\n")

        # if post-hoc test is true
        if ph:
            # perform multiple pairwise comparison (Tukey HSD)
            m_comp = pairwise_tukeyhsd(endog=table[res], groups=table[xfac], alpha=phalpha)
            print("\nPost-hoc Tukey HSD test\n")
            print(m_comp, "\n")

        print("ANOVA Assumption tests\n")
        print("Shapiro-Wilk (P-value):", pvalue1, "\n")
        print("Bartlett (P-value):", pvalue2, "\n")

    def lin_reg(self, df="dataframe", y=None, x=None):
        if x is None or y is None:
            print("Error:Provide proper column names for X and Y variables\n")
            sys.exit(1)
        if type(x) is not list or type(y) is not list:
            print("Error:X or Y column names should be list\n")
            sys.exit(1)
        self.X = df[x].to_numpy()
        self.Y = df[y].to_numpy()

        # number of independent variables
        p = len(x)
        # number of parameter estimates (+1 for intercept and slopes)
        e = p+1
        # number of samples/observations
        n = len(df[y])

        # run regression
        reg_out = LinearRegression().fit(self.X, self.Y)
        # coefficient  of determination
        r_sq = round(reg_out.score(self.X, self.Y), 4)
        # Correlation coefficient (r)
        r = round(np.sqrt(r_sq), 4)
        # Adjusted r-Squared
        r_sq_adj = round(1 - (1 - r_sq) * ((n - 1)/(n-p-1)), 4)
        # RMSE
        rmse = round(np.sqrt(1-r_sq) * np.std(self.Y), 4)
        # intercept and slopes
        reg_intercept = reg_out.intercept_
        reg_slopes = reg_out.coef_
        # predicted values
        self.y_hat = reg_out.predict(self.X)
        # residuals
        self.residuals = self.Y - self.y_hat
        eq = ""
        for i in range(p):
            eq = eq+' + '+ '(' + str(round(reg_slopes[0][i], 4))+'*'+x[i] + ')'

        self.reg_eq = str(round(reg_intercept[0], 4)) + eq

        # sum of squares
        regSS = np.sum((self.y_hat - np.mean(self.Y)) ** 2)  # variation explained by linear model
        residual_sse = np.sum( (self.Y-self.y_hat) ** 2 ) # remaining variation
        sst = np.sum( (self.Y-np.mean(self.Y)) ** 2 ) # total variation

        # variance and std error
        # Residual variance
        sigma_sq_hat = round(residual_sse/(n-e), 4)
        # residual std dev
        res_stdev = round(np.sqrt(sigma_sq_hat))
        # standardized residuals
        self.std_residuals = self.residuals/res_stdev

        # https://stackoverflow.com/questions/22381497/python-scikit-learn-linear-model-parameter-standard-error
        # std error
        X_mat = np.empty(shape=(n, e), dtype=np.float)
        X_mat[:, 0] = 1
        X_mat[:, 1:e] = self.X
        var_hat = np.linalg.inv(X_mat.T @ X_mat) * sigma_sq_hat
        standard_error = []
        for param in range(e):
            standard_error.append(round(np.sqrt(var_hat[param, param]), 4))

        # t = b1 / SE
        params = list(chain(*[["Intercept"], x]))
        estimates = list(chain(*[[reg_intercept[0]], reg_slopes[0]]))
        tabulate_list = []
        for param in range(e):
            tabulate_list.append([params[param], estimates[param], standard_error[param],
                                  estimates[param]/standard_error[param],
                                  '%.4E' % Decimal(stats.t.sf(np.abs(estimates[param]/standard_error[param]), n-1)*2)   ])

        # anova
        anova_table = []
        anova_table.append(["Model", p, regSS, round(regSS/p, 4), round((regSS/p)/(residual_sse/(n-e)), 4),
                            '%.4E' % Decimal(stats.f.sf((regSS/p)/(residual_sse/(n-e)), p, n-e))])
        anova_table.append(["Error", n-e, residual_sse, round(residual_sse/(n-e), 4), "", ""])
        anova_table.append(["Total", n-1, sst, "", "", ""])

        print("\nRegression equation:\n")
        print(self.reg_eq)
        print("\nRegression Summary:")
        print(tabulate([["Dependent variables", x], ["Independent variables", y],
                        ["Coefficient of determination (r-squared)", r_sq], ["Adjusted r-squared)", r_sq_adj],
                        ["Correlation coefficient (r)", r],
                        ["Root Mean Square Error (RMSE)", rmse], ["Adjusted r-squared)", r_sq_adj],
                        ["Mean of Y", round(np.mean(self.Y), 4)], ["Residual standard error", round(np.sqrt(sigma_sq_hat), 4)],
                        ["No. of Observations", n]], "\n"))
        print("\nRegression Coefficients:\n")
        print(tabulate(tabulate_list, headers=["Parameter", "Estimate", "Std Error", "t-value", "P-value Pr(>|t|)"]), "\n")
        print("\nANOVA Summary:\n")
        print(tabulate(anova_table, headers=["Source", "Df", "Sum Squares", "Mean Squares", "F", "Pr(>F)"]),
              "\n")

    def ttsam(df='dataframe', xfac=None, res=None, evar=True):
        # d = pd.read_csv(table)
        if xfac and res is None:
            print("Error: xfac or res variable is missing")
            sys.exit(1)
        levels = df[xfac].unique()
        if len(levels) > 2:
            print("Error: there must be only two levels")
            sys.exit(1)
        a_val = df.loc[df[xfac] == levels[0], res].to_numpy()
        b_val = df.loc[df[xfac] == levels[1], res].to_numpy()
        a_count, b_count = len(a_val), len(b_val)
        count = [a_count, b_count]
        mean = df.groupby(xfac)[res].mean().to_numpy()
        sem = df.groupby(xfac)[res].sem().to_numpy()
        # degree of freedom
        # a_count, b_count = np.split(count, 2)
        dfa = a_count - 1
        dfb = b_count - 1
        # sample variance
        var_a = np.var(a_val, ddof=1)
        var_b = np.var(b_val, ddof=1)
        mean_diff = mean[0] - mean[1]
        # variable 95% CI
        varci_low = []
        varci_up = []
        tcritvar = [(stats.t.ppf((1 + 0.95) / 2, dfa)), (stats.t.ppf((1 + 0.95) / 2, dfb))]
        for i in range(len(levels)):
            varci_low.append(mean[i] - (tcritvar[i] * sem[i]))
            varci_up.append(mean[i] + (tcritvar[i] * sem[i]))

        var_test = 'equal'
        # perform levene to check for equal variances
        w, pvalue = stats.levene(a_val, b_val)
        if pvalue < 0.05:
            print(colored("Warning: the two group variance are not equal. Rerun the test with evar=False"))

        if evar is True:
            # pooled variance
            p_var = (dfa * var_a + dfb * var_b) / (dfa + dfb)
            # std error
            se = np.sqrt(p_var * (1.0 / a_count + 1.0 / b_count))
            dfr = dfa + dfb
        else:
            # Welch's t-test for unequal variance
            # calculate se
            a_temp = var_a / a_count
            b_temp = var_b / b_count
            dfr = ((a_temp + b_temp) ** 2) / ((a_temp ** 2) / (a_count - 1) + (b_temp ** 2) / (b_count - 1))
            se = np.sqrt(a_temp + b_temp)
            var_test = 'unequal'

        tval = np.divide(mean_diff, se)
        oneside_pval = stats.t.sf(np.abs(tval), dfr)
        twoside_pval = oneside_pval * 2
        # 95% CI for diff
        # 2.306 t critical at 0.05
        tcritdiff = stats.t.ppf((1 + 0.95) / 2, dfr)
        diffci_low = mean_diff - (tcritdiff * se)
        diffci_up = mean_diff + (tcritdiff * se)

        # print results
        print("\ntwo sample", levels, "t-test with", var_test, "variance", "\n")
        print(tabulate([["Mean diff", mean_diff], ["t", tval], ["std error", se], ["df", dfr],
                        ["P-value (one-tail)", oneside_pval], ["P-value (two-tail)", twoside_pval],
                        ["Lower 95%", diffci_low], ["Upper 95%", diffci_up]]), "\n")
        print("Parameter estimates\n")
        print(tabulate([[levels[0], count[0], mean[0], sem[0], varci_low[0], varci_low[1]], [levels[1], count[1],
                                                                                             mean[1], sem[1],
                                                                                             varci_up[0], varci_up[1]]],
                       headers=["Level", "Number", "Mean", "Std Error",
                                "Lower 95%", "Upper 95%"]), "\n")

        fig = plt.figure()
        df.boxplot(column=res, by=xfac, grid=False)
        plt.ylabel(res)
        plt.savefig('ttsam_boxplot.png', format='png', bbox_inches='tight', dpi=300)

    def chisq(df='dataframe'):
        # d = pd.read_csv(table, index_col=0)
        tabulate_list = []
        chi_ps, p_ps, dof_ps, expctd_ps = stats.chi2_contingency(df.to_dict('split')['data'])
        tabulate_list.append(["Pearson", dof_ps, chi_ps, p_ps])
        chi_ll, p_ll, dof_ll, expctd_ll = stats.chi2_contingency(df.to_dict('split')['data'], lambda_="log-likelihood")
        tabulate_list.append(["Log-likelihood", dof_ll, chi_ll, p_ll])

        mosaic_dict = dict()
        m = df.to_dict('split')

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                mosaic_dict[(m['index'][i], m['columns'][j])] = m['data'][i][j]

        print("\nChi-squared test\n")
        print(tabulate(tabulate_list, headers=["Test", "Df", "Chi-square", "P-value"]))
        print("\nExpected frequency counts\n")
        print(tabulate(expctd_ps, headers=df.to_dict('split')['columns'], showindex="always"))

        labels = lambda k: "" if mosaic_dict[k] != 0 else ""
        mosaic(mosaic_dict, labelizer=labels)
        plt.savefig('mosaic.png', format='png', bbox_inches='tight', dpi=300)

class help:
    def __init__(self):
        pass

    @staticmethod
    def extract_seq():
        text = """
        Manhatten plot

        bioinfokit.analys.extract_seq(file, id)

        Parameters:
        ------------
        file : input FASTA file from which sequneces to be extracted
        id   : sequence ID file

        Returns:
        Extracted sequences in FASTA format file in same directory (out.fasta )

        Example: https://reneshbedre.github.io/blog/extrseq.html
        """

        print(text)

