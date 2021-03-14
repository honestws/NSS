import torch


class Solution(torch.nn.Module):
    def __init__(self):
        super(Solution, self).__init__()

    def forward(self, a, b):
        inverse_matrix = torch.inverse(torch.matmul(a, a.permute(1, 0)))
        solution = torch.matmul(torch.matmul(a.permute(1, 0), inverse_matrix), b)
        return solution
